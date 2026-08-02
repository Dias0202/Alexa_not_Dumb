from __future__ import annotations

import json
from pathlib import Path


def test_modelo_tem_carrier_phrase_sem_dialog_directive() -> None:
    caminho = Path(__file__).resolve().parents[1] / "models" / "pt-BR.json"
    modelo = json.loads(caminho.read_text(encoding="utf-8"))["interactionModel"]
    pergunta = next(
        intent
        for intent in modelo["languageModel"]["intents"]
        if intent["name"] == "PerguntaIntent"
    )
    slot = pergunta["slots"][0]

    assert slot["type"] == "AMAZON.SearchQuery"
    assert all(
        "{pergunta}" in amostra and amostra != "{pergunta}"
        for amostra in pergunta["samples"]
    )
    assert "dialog" not in modelo
