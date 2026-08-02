"""Carregamento e validação da configuração externa da skill."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import boto3

CHAVE_CONFIG = "config/llm.json"
CAMINHO_CONFIG_LOCAL = Path(__file__).parent / CHAVE_CONFIG
PROVEDORES_SUPORTADOS = frozenset({"groq", "gemini", "local"})
_cache: dict[str, Any] | None = None


class ConfiguracaoErro(RuntimeError):
    """Indica configuração ausente ou inválida, sem expor segredos."""


def _texto_obrigatorio(valor: object, caminho: str) -> None:
    if not isinstance(valor, str) or not valor.strip():
        raise ConfiguracaoErro(f"campo obrigatório inválido: {caminho}")


def validar(configuracao: object) -> dict[str, Any]:
    """Valida apenas a estrutura necessária à fila de provedores ativa."""
    if not isinstance(configuracao, dict):
        raise ConfiguracaoErro("a configuração deve ser um objeto JSON")

    ordem = configuracao.get("ordem")
    if not isinstance(ordem, list) or not ordem:
        raise ConfiguracaoErro("ordem deve conter ao menos um provedor")
    if len(ordem) != len(set(ordem)):
        raise ConfiguracaoErro("ordem não pode repetir provedores")

    perfil = configuracao.get("perfil", "")
    if not isinstance(perfil, str):
        raise ConfiguracaoErro("perfil deve ser texto")

    for nome in ordem:
        if nome not in PROVEDORES_SUPORTADOS:
            raise ConfiguracaoErro("provedor não suportado na ordem")
        dados = configuracao.get(nome)
        if not isinstance(dados, Mapping):
            raise ConfiguracaoErro(f"configuração ausente para {nome}")
        _texto_obrigatorio(dados.get("modelo"), f"{nome}.modelo")
        if nome == "local":
            url = dados.get("url")
            _texto_obrigatorio(url, "local.url")
            if not str(url).startswith("https://"):
                raise ConfiguracaoErro("local.url deve usar HTTPS")
            _texto_obrigatorio(dados.get("token"), "local.token")
        else:
            _texto_obrigatorio(dados.get("api_key"), f"{nome}.api_key")

    return configuracao


def carregar() -> dict[str, Any]:
    """Lê a configuração local ou do S3 uma vez por container e a mantém em cache."""
    global _cache
    if _cache is not None:
        return _cache

    if CAMINHO_CONFIG_LOCAL.is_file():
        try:
            conteudo_local = CAMINHO_CONFIG_LOCAL.read_text(encoding="utf-8")
            _cache = validar(json.loads(conteudo_local))
            return _cache
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as erro:
            raise ConfiguracaoErro(
                "não foi possível interpretar a configuração local"
            ) from erro

    bucket = os.environ.get("S3_PERSISTENCE_BUCKET")
    if not bucket:
        raise ConfiguracaoErro("bucket de configuração não disponível")

    try:
        cliente = boto3.client("s3")
        objeto = cliente.get_object(Bucket=bucket, Key=CHAVE_CONFIG)
        conteudo = objeto["Body"].read().decode("utf-8")
        _cache = validar(json.loads(conteudo))
    except ConfiguracaoErro:
        raise
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise ConfiguracaoErro("não foi possível interpretar a configuração") from erro
    except Exception as erro:
        raise ConfiguracaoErro("não foi possível carregar a configuração") from erro

    return _cache


def limpar_cache() -> None:
    """Remove o cache; reservado a testes e à rotação controlada de configuração."""
    global _cache
    _cache = None
