"""Health check endpoints for Brainerd and its dependencies."""

from fastapi import APIRouter

from app.services import google_ai, ollama

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health():
    return {"status": "ok", "service": "brainerd"}


@router.get("/ollama")
async def ollama_health():
    return await ollama.health_check()


@router.get("/google")
async def google_health():
    return await google_ai.health_check()


@router.get("/all")
async def full_health():
    ol = await ollama.health_check()
    goog = await google_ai.health_check()
    overall = "ok" if ol["status"] == "ok" else "degraded"
    return {
        "status": overall,
        "ollama": ol,
        "google_ai": goog,
    }
