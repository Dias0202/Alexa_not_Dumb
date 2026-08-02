from __future__ import annotations

from collections.abc import Mapping

import proxy
from fastapi.testclient import TestClient


class ClienteOllamaFalso:
    async def post(self, _url: str, json: Mapping[str, object]):
        self.corpo = json
        return RespostaOllamaFalsa()

    async def aclose(self) -> None:
        return None


class RespostaOllamaFalsa:
    status_code = 200

    @staticmethod
    def json() -> dict[str, object]:
        return {"message": {"content": "resposta local"}}


def test_proxy_exige_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("PROXY_TOKEN", "token-de-teste")
    monkeypatch.setattr(
        proxy.httpx, "AsyncClient", lambda **_kwargs: ClienteOllamaFalso()
    )

    with TestClient(proxy.app) as cliente:
        resposta = cliente.post("/api/chat", json={"model": "llama"})

    assert resposta.status_code == 401


def test_proxy_repassa_corpo_autorizado_sem_stream(monkeypatch) -> None:
    monkeypatch.setenv("PROXY_TOKEN", "token-de-teste")
    cliente_ollama = ClienteOllamaFalso()
    monkeypatch.setattr(proxy.httpx, "AsyncClient", lambda **_kwargs: cliente_ollama)

    with TestClient(proxy.app) as cliente:
        resposta = cliente.post(
            "/api/chat",
            headers={"Authorization": "Bearer token-de-teste"},
            json={"model": "llama", "stream": True},
        )

    assert resposta.status_code == 200
    assert resposta.json() == {"message": {"content": "resposta local"}}
    assert cliente_ollama.corpo["stream"] is False
