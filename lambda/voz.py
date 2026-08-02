"""Normalização de texto gerado para reprodução por voz."""

from __future__ import annotations

import re

LIMITE = 600
LINK = re.compile(r"https?://\S+", re.IGNORECASE)
LINK_MARKDOWN = re.compile(r"\[([^\]]+)\]\([^)]*\)")
MARCACAO = re.compile(r"[*_`#>~]")
PREFIXO_LISTA = re.compile(r"(?:^|\n)\s*(?:[-+]|\d+[.)])\s*", re.MULTILINE)


class RespostaVazia(ValueError):
    """Texto que não pode ser dito pela Alexa após normalização."""


def normalizar(texto: str, limite: int = LIMITE) -> str:
    """Remove marcação e corta respostas extensas em um limite apropriado à voz."""
    if not isinstance(texto, str):
        raise TypeError("texto deve ser uma string")

    texto = LINK_MARKDOWN.sub(r"\1", texto)
    texto = LINK.sub("", texto)
    texto = PREFIXO_LISTA.sub(" ", texto)
    texto = MARCACAO.sub("", texto)
    texto = " ".join(texto.split())
    if not texto:
        raise RespostaVazia("resposta vazia após normalização")

    if len(texto) <= limite:
        return texto

    corte = texto[:limite]
    fim = max(corte.rfind("."), corte.rfind("!"), corte.rfind("?"))
    return corte[: fim + 1] if fim > 150 else f"{corte.rstrip()}..."


def escapar_ssml(texto: str) -> str:
    """Escapa texto dinâmico antes de inseri-lo no SSML da resposta progressiva."""
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
