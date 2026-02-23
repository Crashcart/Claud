"""Google Gemini AI service — optional, only loaded when API key is present."""

import logging
from collections.abc import AsyncGenerator

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_model():
    """Lazy-load google.generativeai to avoid import errors when not configured."""
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=settings.google_ai_api_key)
        return genai.GenerativeModel(settings.google_ai_model)
    except ImportError:
        raise RuntimeError("google-generativeai package not installed")


def _to_gemini_history(messages: list[dict]) -> list[dict]:
    """Convert OpenAI-style messages to Gemini history format."""
    history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    return history


async def chat(messages: list[dict], stream: bool = False) -> dict | AsyncGenerator:
    """Send messages to Google Gemini."""
    if not settings.google_enabled:
        raise RuntimeError("Google AI is not configured (GOOGLE_AI_API_KEY not set)")

    import asyncio

    model = _get_model()

    # Extract system prompt if present
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    chat_messages = [m for m in messages if m["role"] != "system"]

    history = _to_gemini_history(chat_messages[:-1]) if len(chat_messages) > 1 else []
    last_message = chat_messages[-1]["content"] if chat_messages else ""

    if system_parts:
        last_message = f"{system_parts[0]}\n\n{last_message}"

    chat_session = model.start_chat(history=history)

    if stream:
        return _stream_google(chat_session, last_message)

    # Gemini SDK is sync — run in thread pool
    response = await asyncio.to_thread(chat_session.send_message, last_message)
    content = response.text
    tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0

    return {
        "content": content,
        "tokens": tokens,
        "provider": "google",
    }


async def _stream_google(chat_session, message: str) -> AsyncGenerator[str, None]:
    import asyncio

    response = await asyncio.to_thread(
        chat_session.send_message, message, stream=True
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text


async def health_check() -> dict:
    if not settings.google_enabled:
        return {"status": "disabled", "detail": "GOOGLE_AI_API_KEY not set"}
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=settings.google_ai_api_key)
        return {
            "status": "ok",
            "model": settings.google_ai_model,
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
