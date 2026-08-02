"""Proxy autenticado entre a Internet pública e o Ollama local."""

from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")


def _token_configurado() -> str:
    token = os.getenv("PROXY_TOKEN")
    if not token:
        raise RuntimeError("PROXY_TOKEN deve ser definido antes de iniciar o proxy")
    return token


@asynccontextmanager
async def lifespan(app: FastAPI):
    _token_configurado()
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(20.0))
    yield
    await app.state.http.aclose()


app = FastAPI(
    title="Proxy Ollama Alexa", docs_url=None, redoc_url=None, lifespan=lifespan
)


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/chat")
async def chat(
    requisicao: Request, authorization: str = Header(default="")
) -> JSONResponse:
    esperado = f"Bearer {_token_configurado()}"
    if not secrets.compare_digest(authorization, esperado):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="não autorizado"
        )

    try:
        corpo = await requisicao.json()
    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="JSON inválido"
        ) from erro
    if not isinstance(corpo, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="corpo deve ser objeto"
        )
    corpo["stream"] = False

    try:
        resposta = await requisicao.app.state.http.post(
            f"{OLLAMA_URL}/api/chat", json=corpo
        )
        conteudo = resposta.json()
    except httpx.HTTPError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama indisponível",
        ) from erro
    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="resposta Ollama inválida"
        ) from erro

    return JSONResponse(status_code=resposta.status_code, content=conteudo)
