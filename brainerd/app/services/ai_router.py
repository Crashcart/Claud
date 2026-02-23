"""AI Router — dispatches requests to Ollama or Google based on config/request."""

import logging
from collections.abc import AsyncGenerator
from typing import Literal

from app.config import get_settings
from app.services import google_ai, ollama

logger = logging.getLogger(__name__)
settings = get_settings()

Provider = Literal["ollama", "google", "auto"]


async def complete(
    messages: list[dict],
    provider: Provider | None = None,
    stream: bool = False,
) -> dict | AsyncGenerator:
    """
    Route a chat request to the appropriate AI backend.

    Priority:
      1. Explicit provider in request
      2. Config: ai_provider setting
      3. Auto: prefer Google if key is set, else Ollama
    """
    resolved = _resolve_provider(provider)
    logger.debug("AI router: using provider=%s stream=%s", resolved, stream)

    if resolved == "google":
        return await google_ai.chat(messages, stream=stream)
    return await ollama.chat(messages, stream=stream)


def _resolve_provider(requested: Provider | None) -> Literal["ollama", "google"]:
    p = requested or settings.ai_provider

    if p == "google":
        if not settings.google_enabled:
            logger.warning("Google AI requested but not configured, falling back to Ollama")
            return "ollama"
        return "google"

    if p == "ollama":
        return "ollama"

    # "auto"
    if settings.google_enabled:
        return "google"
    return "ollama"
