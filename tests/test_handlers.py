from __future__ import annotations

import lambda_function


def test_lancamento_nao_envia_diretiva_de_dialogo() -> None:
    evento = {
        "version": "1.0",
        "session": {
            "new": True,
            "sessionId": "SessionId.teste",
            "application": {"applicationId": "amzn1.ask.skill.teste"},
            "user": {"userId": "amzn1.ask.account.teste"},
        },
        "context": {
            "System": {
                "application": {"applicationId": "amzn1.ask.skill.teste"},
                "user": {"userId": "amzn1.ask.account.teste"},
                "device": {"deviceId": "dispositivo.teste", "supportedInterfaces": {}},
                "apiEndpoint": "https://api.amazonalexa.com",
                "apiAccessToken": "",
            }
        },
        "request": {
            "type": "LaunchRequest",
            "requestId": "EdwRequestId.teste",
            "timestamp": "2026-08-02T17:30:00Z",
            "locale": "pt-BR",
        },
    }

    resposta = lambda_function.lambda_handler(evento, None)

    assert resposta["response"].get("directives", []) == []
    assert resposta["response"]["shouldEndSession"] is False
    assert resposta["response"]["outputSpeech"] == {
        "type": "PlainText",
        "text": "Oi. Para perguntar, diga: pergunte, e a sua pergunta.",
    }


def test_historico_descarta_itens_malformados_e_limita_tamanho() -> None:
    entrada = [
        {"role": "user", "content": "pergunta"},
        {"role": "system", "content": "não deve viajar"},
        {"role": "assistant", "content": 1},
        {"role": "assistant", "content": "resposta"},
    ]

    assert lambda_function._historico_valido(entrada) == [
        {"role": "user", "content": "pergunta"},
        {"role": "assistant", "content": "resposta"},
    ]
