from __future__ import annotations

import urllib.error

import llm
import pytest

MENSAGENS = [{"role": "user", "content": "Olá"}]


def test_gerar_faz_fallback_apos_erro_http(monkeypatch: pytest.MonkeyPatch) -> None:
    configuracao = {
        "ordem": ["groq", "gemini"],
        "groq": {"api_key": "a", "modelo": "a"},
        "gemini": {"api_key": "b", "modelo": "b"},
    }
    chamadas: list[str] = []

    def falha(*_args: object) -> str:
        chamadas.append("groq")
        raise urllib.error.HTTPError("https://exemplo", 429, "", {}, None)

    def sucesso(*_args: object) -> str:
        chamadas.append("gemini")
        return "Resposta válida"

    monkeypatch.setattr(llm.config, "carregar", lambda: configuracao)
    monkeypatch.setitem(llm.PROVEDORES, "groq", falha)
    monkeypatch.setitem(llm.PROVEDORES, "gemini", sucesso)

    assert llm.gerar(MENSAGENS) == "Resposta válida"
    assert chamadas == ["groq", "gemini"]


def test_gerar_rejeita_resposta_vazia_e_tenta_proximo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuracao = {
        "ordem": ["groq", "gemini"],
        "groq": {"api_key": "a", "modelo": "a"},
        "gemini": {"api_key": "b", "modelo": "b"},
    }
    monkeypatch.setattr(llm.config, "carregar", lambda: configuracao)
    monkeypatch.setitem(llm.PROVEDORES, "groq", lambda *_args: "   ")
    monkeypatch.setitem(llm.PROVEDORES, "gemini", lambda *_args: "ok")

    assert llm.gerar(MENSAGENS) == "ok"


def test_gerar_informa_indisponibilidade_quando_todos_falham(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuracao = {"ordem": ["groq"], "groq": {"api_key": "a", "modelo": "a"}}
    monkeypatch.setattr(llm.config, "carregar", lambda: configuracao)
    monkeypatch.setitem(
        llm.PROVEDORES, "groq", lambda *_args: (_ for _ in ()).throw(OSError())
    )

    with pytest.raises(llm.ProvedorIndisponivel, match="groq:OSError"):
        llm.gerar(MENSAGENS)


def test_gemini_separa_system_instruction(monkeypatch: pytest.MonkeyPatch) -> None:
    capturado: dict[str, object] = {}

    def post(_url: str, corpo: dict[str, object], *_args: object) -> dict[str, object]:
        capturado.update(corpo)
        return {"candidates": [{"content": {"parts": [{"text": "oi"}]}}]}

    monkeypatch.setattr(llm, "_post_json", post)
    texto = llm._gemini(
        {"api_key": "segredo", "modelo": "flash"},
        [
            {"role": "system", "content": "sistema"},
            {"role": "user", "content": "pergunta"},
        ],
        1.0,
    )

    assert texto == "oi"
    assert capturado["systemInstruction"] == {"parts": [{"text": "sistema"}]}
    assert capturado["contents"] == [{"role": "user", "parts": [{"text": "pergunta"}]}]
