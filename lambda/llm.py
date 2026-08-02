"""Roteador de provedores de inferência com fallback em cadeia."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import config

logger = logging.getLogger(__name__)

PRAZO_TOTAL = 6.0
PRAZO_POR_PROVEDOR = 5.0
PRAZO_MINIMO = 1.5
MAX_TOKENS = 220

Mensagem = Mapping[str, str]
ClienteProvedor = Callable[[Mapping[str, Any], Sequence[Mensagem], float], str]


class ProvedorIndisponivel(RuntimeError):
    """Indica que nenhum provedor retornou uma resposta aproveitável."""


def _post_json(
    url: str, corpo: Mapping[str, Any], cabecalhos: Mapping[str, str], timeout: float
) -> dict[str, Any]:
    dados = json.dumps(corpo).encode("utf-8")
    requisicao = urllib.request.Request(
        url, data=dados, headers=dict(cabecalhos), method="POST"
    )
    with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
        retorno = json.loads(resposta.read().decode("utf-8"))
    if not isinstance(retorno, dict):
        raise ValueError("resposta do provedor não é um objeto JSON")
    return retorno


def _conteudo_groq(dados: Mapping[str, Any]) -> str:
    try:
        texto = dados["choices"][0]["message"]["content"]
    except (IndexError, KeyError, TypeError) as erro:
        raise ValueError("resposta Groq sem conteúdo") from erro
    if not isinstance(texto, str):
        raise ValueError("conteúdo Groq inválido")
    return texto


def _groq(cfg: Mapping[str, Any], mensagens: Sequence[Mensagem], timeout: float) -> str:
    corpo = {
        "model": cfg["modelo"],
        "messages": list(mensagens),
        "max_tokens": MAX_TOKENS,
        "temperature": 0.6,
    }
    cabecalhos = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    dados = _post_json(
        "https://api.groq.com/openai/v1/chat/completions", corpo, cabecalhos, timeout
    )
    return _conteudo_groq(dados)


def _gemini(
    cfg: Mapping[str, Any], mensagens: Sequence[Mensagem], timeout: float
) -> str:
    sistema = next((m["content"] for m in mensagens if m["role"] == "system"), None)
    conteudos = [
        {
            "role": "model" if mensagem["role"] == "assistant" else "user",
            "parts": [{"text": mensagem["content"]}],
        }
        for mensagem in mensagens
        if mensagem["role"] != "system"
    ]
    corpo: dict[str, Any] = {
        "contents": conteudos,
        "generationConfig": {"maxOutputTokens": MAX_TOKENS, "temperature": 0.6},
    }
    if sistema:
        corpo["systemInstruction"] = {"parts": [{"text": sistema}]}

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{cfg['modelo']}:generateContent?key={cfg['api_key']}"
    )
    dados = _post_json(url, corpo, {"Content-Type": "application/json"}, timeout)
    try:
        texto = dados["candidates"][0]["content"]["parts"][0]["text"]
    except (IndexError, KeyError, TypeError) as erro:
        raise ValueError("resposta Gemini sem conteúdo") from erro
    if not isinstance(texto, str):
        raise ValueError("conteúdo Gemini inválido")
    return texto


def _local(
    cfg: Mapping[str, Any], mensagens: Sequence[Mensagem], timeout: float
) -> str:
    corpo = {
        "model": cfg["modelo"],
        "messages": list(mensagens),
        "stream": False,
        "options": {"num_predict": MAX_TOKENS},
    }
    cabecalhos = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['token']}",
    }
    dados = _post_json(
        f"{str(cfg['url']).rstrip('/')}/api/chat", corpo, cabecalhos, timeout
    )
    try:
        texto = dados["message"]["content"]
    except (KeyError, TypeError) as erro:
        raise ValueError("resposta local sem conteúdo") from erro
    if not isinstance(texto, str):
        raise ValueError("conteúdo local inválido")
    return texto


PROVEDORES: Mapping[str, ClienteProvedor] = {
    "groq": _groq,
    "gemini": _gemini,
    "local": _local,
}


def gerar(mensagens: Sequence[Mensagem], prazo_total: float = PRAZO_TOTAL) -> str:
    """Executa a fila configurada sem vazar prompts, chaves ou URLs em log."""
    configuracao = config.carregar()
    inicio = time.monotonic()
    ultimo_erro: Exception | None = None

    for nome in configuracao["ordem"]:
        restante = prazo_total - (time.monotonic() - inicio)
        if restante < PRAZO_MINIMO:
            logger.warning("Prazo esgotado antes de tentar provedor=%s", nome)
            break

        try:
            marca = time.monotonic()
            texto = PROVEDORES[nome](
                configuracao[nome], mensagens, min(restante, PRAZO_POR_PROVEDOR)
            )
            if not texto.strip():
                raise ValueError("resposta vazia")
            logger.info(
                "Provedor respondeu provedor=%s duracao_s=%.2f",
                nome,
                time.monotonic() - marca,
            )
            return texto.strip()
        except urllib.error.HTTPError as erro:
            ultimo_erro = erro
            logger.warning(
                "Provedor respondeu com erro provedor=%s status=%s", nome, erro.code
            )
        except Exception as erro:
            ultimo_erro = erro
            logger.warning(
                "Provedor falhou provedor=%s tipo=%s", nome, type(erro).__name__
            )

    motivo = type(ultimo_erro).__name__ if ultimo_erro else "prazo_esgotado"
    raise ProvedorIndisponivel(f"nenhum provedor respondeu ({motivo})")
