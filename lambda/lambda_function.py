"""Handlers da skill Alexa-hosted."""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from collections.abc import Mapping
from typing import Any

import llm
import voz
from ask_sdk_core.dispatch_components import (
    AbstractExceptionHandler,
    AbstractRequestHandler,
)
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_model import Intent
from ask_sdk_model.dialog import ElicitSlotDirective

import config

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


def montar_prompt_sistema() -> str:
    """Combina o comportamento estável com o perfil não versionado do usuário."""
    perfil = config.carregar().get("perfil", "")
    return f"{PROMPT_BASE} {perfil}".strip()


def elicitar() -> ElicitSlotDirective:
    """Reabre o microfone com slot limpo para não repetir a pergunta anterior."""
    return ElicitSlotDirective(
        slot_to_elicit=SLOT,
        updated_intent=Intent(name=INTENT, slots={}),
    )


def falar_espera(handler_input: Any, texto: str = "Só um instante.") -> None:
    """Emite resposta progressiva por melhor esforço sem afetar a resposta final."""
    try:
        sistema = handler_input.request_envelope.context.system
        corpo = {
            "header": {"requestId": handler_input.request_envelope.request.request_id},
            "directive": {
                "type": "VoicePlayer.Speak",
                "speech": f"<speak>{voz.escapar_ssml(texto)}</speak>",
            },
        }
        requisicao = urllib.request.Request(
            f"{sistema.api_endpoint}/v1/directives",
            data=json.dumps(corpo).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {sistema.api_access_token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(requisicao, timeout=1.0):
            pass
    except Exception as erro:  # resposta progressiva não pode interromper o turno
        logger.info("Resposta progressiva ignorada tipo=%s", type(erro).__name__)


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


def _pergunta(handler_input: Any) -> str:
    slots = handler_input.request_envelope.request.intent.slots or {}
    slot = slots.get(SLOT)
    valor = getattr(slot, "value", None)
    return valor.strip() if isinstance(valor, str) else ""


class LaunchHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: Any) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: Any) -> Any:
        handler_input.attributes_manager.session_attributes["historico"] = []
        return (
            handler_input.response_builder.speak("Oi. Pode perguntar.")
            .ask("Estou ouvindo.")
            .add_directive(elicitar())
            .response
        )


class PerguntaHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: Any) -> bool:
        return is_intent_name(INTENT)(handler_input)

    def handle(self, handler_input: Any) -> Any:
        inicio = time.monotonic()
        pergunta = _pergunta(handler_input)
        if not pergunta:
            return (
                handler_input.response_builder.speak("Não peguei. Pode repetir?")
                .ask("Pode repetir?")
                .add_directive(elicitar())
                .response
            )

        atributos = handler_input.attributes_manager.session_attributes
        historico = _historico_valido(atributos.get("historico", []))
        mensagens = [{"role": "system", "content": montar_prompt_sistema()}]
        mensagens.extend(historico)
        mensagens.append({"role": "user", "content": pergunta})
        falar_espera(handler_input)

        restante = llm.PRAZO_TOTAL - (time.monotonic() - inicio)
        if restante < llm.PRAZO_MINIMO:
            texto = "Demorei demais aqui. Pergunta de novo?"
        else:
            try:
                texto = voz.normalizar(llm.gerar(mensagens, restante))
            except (llm.ProvedorIndisponivel, voz.RespostaVazia, ValueError) as erro:
                logger.error(
                    "Falha em todos os provedores tipo=%s", type(erro).__name__
                )
                texto = "Não consegui falar com o modelo agora. Tenta de novo?"
            else:
                historico.extend(
                    [
                        {"role": "user", "content": pergunta},
                        {"role": "assistant", "content": texto},
                    ]
                )
                atributos["historico"] = historico[-MAX_MENSAGENS:]

        logger.info("Turno concluído duracao_s=%.2f", time.monotonic() - inicio)
        return (
            handler_input.response_builder.speak(texto)
            .ask("Mais alguma coisa?")
            .add_directive(elicitar())
            .response
        )


class EncerrarHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: Any) -> bool:
        return is_intent_name("AMAZON.StopIntent")(handler_input) or is_intent_name(
            "AMAZON.CancelIntent"
        )(handler_input)

    def handle(self, handler_input: Any) -> Any:
        return (
            handler_input.response_builder.speak("Até mais.")
            .set_should_end_session(True)
            .response
        )


class AjudaHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: Any) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: Any) -> Any:
        return (
            handler_input.response_builder.speak(
                "Pode me perguntar qualquer coisa. Diga para quando quiser sair."
            )
            .ask("O que você quer saber?")
            .add_directive(elicitar())
            .response
        )


class FallbackHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: Any) -> bool:
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input: Any) -> Any:
        return (
            handler_input.response_builder.speak("Não entendi. Pode falar de novo?")
            .ask("Pode falar de novo?")
            .add_directive(elicitar())
            .response
        )


class SessaoEncerradaHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: Any) -> bool:
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: Any) -> Any:
        motivo = getattr(handler_input.request_envelope.request, "reason", None)
        logger.info("Sessão encerrada motivo=%s", motivo)
        return handler_input.response_builder.response


class ErroGeralHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input: Any, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: Any, exception: Exception) -> Any:
        logger.exception("Erro não tratado tipo=%s", type(exception).__name__)
        if isinstance(exception, config.ConfiguracaoErro):
            texto = "Estou com um problema de configuração. Tenta de novo mais tarde?"
        else:
            texto = "Deu ruim aqui do meu lado. Tenta de novo?"
        return (
            handler_input.response_builder.speak(texto)
            .ask("Tenta de novo?")
            .add_directive(elicitar())
            .response
        )


skill_builder = SkillBuilder()
skill_builder.add_request_handler(LaunchHandler())
skill_builder.add_request_handler(PerguntaHandler())
skill_builder.add_request_handler(EncerrarHandler())
skill_builder.add_request_handler(AjudaHandler())
skill_builder.add_request_handler(FallbackHandler())
skill_builder.add_request_handler(SessaoEncerradaHandler())
skill_builder.add_exception_handler(ErroGeralHandler())

lambda_handler = skill_builder.lambda_handler()
