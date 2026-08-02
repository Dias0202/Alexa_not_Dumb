from __future__ import annotations

import pytest

import config


def configuracao_valida() -> dict[str, object]:
    return {
        "ordem": ["groq", "gemini"],
        "perfil": "Respostas diretas.",
        "groq": {"api_key": "chave", "modelo": "modelo-groq"},
        "gemini": {"api_key": "chave", "modelo": "modelo-gemini"},
    }


def test_validar_aceita_fila_de_provedores() -> None:
    dados = configuracao_valida()

    assert config.validar(dados) is dados


@pytest.mark.parametrize(
    "alteracao",
    [
        {"ordem": []},
        {"ordem": ["groq", "groq"]},
        {"ordem": ["desconhecido"]},
        {"perfil": 1},
    ],
)
def test_validar_rejeita_estrutura_invalida(alteracao: dict[str, object]) -> None:
    dados = configuracao_valida()
    dados.update(alteracao)

    with pytest.raises(config.ConfiguracaoErro):
        config.validar(dados)


def test_validar_exige_https_para_provedor_local() -> None:
    dados = {
        "ordem": ["local"],
        "perfil": "",
        "local": {
            "url": "http://localhost:8080",
            "token": "segredo",
            "modelo": "llama",
        },
    }

    with pytest.raises(config.ConfiguracaoErro, match="HTTPS"):
        config.validar(dados)


def test_carregar_prioriza_arquivo_local_antes_do_s3(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    caminho = tmp_path / "config" / "llm.json"
    caminho.parent.mkdir()
    caminho.write_text(
        '{"ordem":["groq"],"perfil":"","groq":{"api_key":"chave","modelo":"modelo"}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "CAMINHO_CONFIG_LOCAL", caminho)
    monkeypatch.delenv("S3_PERSISTENCE_BUCKET", raising=False)
    config.limpar_cache()

    assert config.carregar()["ordem"] == ["groq"]

    config.limpar_cache()
