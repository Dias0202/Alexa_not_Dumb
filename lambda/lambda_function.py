"""Handler Alexa-hosted com respostas JSON compatíveis com o endpoint ASK."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

INTENT = "PerguntaIntent"
SLOT = "pergunta"
MAX_MENSAGENS = 6
PROMPT_BASE = (
    "Você é um assistente pessoal falado, acessado por um dispositivo Alexa. "
    "Responda sempre em português do Brasil. "
    "Máximo de três frases. Vá direto ao ponto, sem introdução e sem resumo final. "
    "Nunca use listas, títulos, markdown, emoji ou qualquer formatação. "
    "Escreva números por extenso quando forem curtos. "
    "A transcrição de voz pode ter erros; interprete a intenção sem pedir confirmação. "
    "Se não souber, diga que não sabe em uma frase."
)


def _historico_valido(valor: object) -> list[dict[str, str]]:
    if not isinstance(valor, list):
        return []
    mensagens: list[dict[str, str]] = []
    for mensagem in valor[-MAX_MENSAGENS:]:
        if not isinstance(mensagem, Mapping):
            continue
        papel, conteudo = mensagem.get("role"), mensagem.get("content")
        if papel in {"user", "assistant"} and isinstance(conteudo, str):
            mensagens.append({"role": papel, "content": conteudo})
    return mensagens


def _texto_obrigatorio(valor: object) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def _atributos_sessao(evento: Mapping[str, Any]) -> dict[str, Any]:
    sessao = evento.get("session")
    if not isinstance(sessao, Mapping):
        return {}
    atributos = sessao.get("attributes", {})
    return dict(atributos) if isinstance(atributos, Mapping) else {}


def _pergunta(evento: Mapping[str, Any]) -> str:
    requisicao = evento.get("request")
    if not isinstance(requisicao, Mapping):
        return ""
    intent = requisicao.get("intent")
    if not isinstance(intent, Mapping):
        return ""
    slots = intent.get("slots")
    if not isinstance(slots, Mapping):
        return ""
    slot = slots.get(SLOT)
    return _texto_obrigatorio(slot.get("value")) if isinstance(slot, Mapping) else ""


def resposta(
    texto: str,
    *,
    encerrar: bool = False,
    reprompt: str | None = None,
    atributos: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Cria a resposta Alexa nativa, sem objetos serializados pelo SDK."""
    corpo: dict[str, Any] = {
        "outputSpeech": {"type": "PlainText", "text": texto},
        "shouldEndSession": encerrar,
    }
    if not encerrar and reprompt:
        corpo["reprompt"] = {
            "outputSpeech": {"type": "PlainText", "text": reprompt}
        }

    retorno: dict[str, Any] = {"version": "1.0", "response": corpo}
    if atributos is not None:
        retorno["sessionAttributes"] = dict(atributos)
    return retorno


def _resposta_de_pergunta(evento: Mapping[str, Any]) -> dict[str, Any]:
    inicio = time.monotonic()
    pergunta = _pergunta(evento)
    atributos = _atributos_sessao(evento)
    if not pergunta:
        return resposta(
            "Não peguei. Diga: pergunte, e a sua pergunta.",
            reprompt="O que você quer perguntar?",
            atributos=atributos,
        )

    historico = _historico_valido(atributos.get("historico", []))
    try:
        import llm
        import voz

        import config

        perfil = config.carregar().get("perfil", "")
        mensagens = [{"role": "system", "content": f"{PROMPT_BASE} {perfil}".strip()}]
        mensagens.extend(historico)
        mensagens.append({"role": "user", "content": pergunta})

        restante = llm.PRAZO_TOTAL - (time.monotonic() - inicio)
        if restante < llm.PRAZO_MINIMO:
            texto = "Demorei demais aqui. Pergunta de novo?"
        else:
            texto = voz.normalizar(llm.gerar(mensagens, restante))
            historico.extend(
                [
                    {"role": "user", "content": pergunta},
                    {"role": "assistant", "content": texto},
                ]
            )
            atributos["historico"] = historico[-MAX_MENSAGENS:]
    except Exception as erro:
        logger.error("Falha no runtime de inferência tipo=%s", type(erro).__name__)
        texto = "Não consegui falar com o modelo agora. Tenta de novo?"

    logger.info("Turno concluído duracao_s=%.2f", time.monotonic() - inicio)
    return resposta(
        texto,
        reprompt="Mais alguma coisa? Diga: pergunte, e a sua pergunta.",
        atributos=atributos,
    )


def lambda_handler(event: Mapping[str, Any], _context: object) -> dict[str, Any]:
    """Atende requisições ASK sem depender da serialização do SDK."""
    try:
        requisicao = event.get("request")
        if not isinstance(requisicao, Mapping):
            return resposta("Não entendi a solicitação.", encerrar=True)

        tipo = requisicao.get("type")
        atributos = _atributos_sessao(event)
        if tipo == "LaunchRequest":
            atributos["historico"] = []
            return resposta(
                "Oi. Para perguntar, diga: pergunte, e a sua pergunta.",
                reprompt="O que você quer perguntar?",
                atributos=atributos,
            )
        if tipo == "SessionEndedRequest":
            return {"version": "1.0", "response": {}}
        if tipo != "IntentRequest":
            return resposta(
                "Não entendi. Tenta de novo?",
                reprompt="Diga: pergunte, e a sua pergunta.",
                atributos=atributos,
            )

        intent = requisicao.get("intent")
        nome_intent = intent.get("name") if isinstance(intent, Mapping) else None
        if nome_intent == INTENT:
            return _resposta_de_pergunta(event)
        if nome_intent in {"AMAZON.StopIntent", "AMAZON.CancelIntent"}:
            return resposta("Até mais.", encerrar=True, atributos=atributos)
        if nome_intent == "AMAZON.HelpIntent":
            return resposta(
                "Pode me perguntar qualquer coisa. Diga: pergunte, e a sua pergunta.",
                reprompt="O que você quer perguntar?",
                atributos=atributos,
            )
        return resposta(
            "Não entendi. Diga: pergunte, e a sua pergunta.",
            reprompt="O que você quer perguntar?",
            atributos=atributos,
        )
    except Exception as erro:
        logger.exception("Erro não tratado tipo=%s", type(erro).__name__)
        return resposta(
            "Deu ruim aqui do meu lado. Tenta de novo?",
            reprompt="Diga: pergunte, e a sua pergunta.",
            atributos=_atributos_sessao(event),
        )
