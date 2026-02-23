"""Ollama service — local inference via Ollama API."""

import logging
from collections.abc import AsyncGenerator

import httpx
import ollama as ollama_client

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _make_client() -> ollama_client.AsyncClient:
    return ollama_client.AsyncClient(host=settings.ollama_host)


async def chat(
    messages: list[dict],
    model: str | None = None,
    stream: bool = False,
) -> dict | AsyncGenerator:
    """Send messages to Ollama. Returns full response or async generator for streaming."""
    model = model or settings.ollama_model
    client = _make_client()

    if stream:
        return _stream_chat(client, model, messages)

    response = await client.chat(model=model, messages=messages)
    return {
        "content": response.message.content,
        "tokens": (response.eval_count or 0) + (response.prompt_eval_count or 0),
        "provider": "ollama",
    }


async def _stream_chat(
    client: ollama_client.AsyncClient,
    model: str,
    messages: list[dict],
) -> AsyncGenerator[str, None]:
    async for chunk in await client.chat(model=model, messages=messages, stream=True):
        if chunk.message and chunk.message.content:
            yield chunk.message.content


async def health_check() -> dict:
    """Check Ollama is reachable and the model is available."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.ollama_host}/api/tags")
            r.raise_for_status()
            tags = r.json()
        models = [m["name"] for m in tags.get("models", [])]
        return {
            "status": "ok",
            "host": settings.ollama_host,
            "model": settings.ollama_model,
            "model_available": any(settings.ollama_model in m for m in models),
            "available_models": models,
        }
    except Exception as exc:
        logger.warning("Ollama health check failed: %s", exc)
        return {"status": "error", "detail": str(exc)}
