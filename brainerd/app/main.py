"""Brainerd AI — main FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health, rpg
from app.config import get_settings
from app.database.connection import init_db

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("brainerd")

app = FastAPI(
    title="Brainerd AI",
    description=(
        "Local-first AI hub running Ollama (mistral:7b) with optional Google Gemini. "
        "Supports basic chat and RPG game sessions. "
        "Designed for inter-container communication via Docker networking."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow linked containers and any configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(rpg.router)


@app.on_event("startup")
async def startup():
    logger.info("Brainerd AI starting up...")
    await init_db()
    logger.info(
        "DB ready | AI provider: %s | Ollama model: %s | Google enabled: %s",
        settings.ai_provider,
        settings.ollama_model,
        settings.google_enabled,
    )


@app.get("/", tags=["root"])
async def root():
    return {
        "service": "brainerd",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health/all",
        "endpoints": {
            "chat_rest": "POST /chat/",
            "chat_ws": "WS /chat/ws/{session_id}",
            "rpg_new": "POST /rpg/games",
            "rpg_action": "POST /rpg/games/{id}/action",
        },
        "ai": {
            "provider": settings.ai_provider,
            "ollama_model": settings.ollama_model,
            "google_enabled": settings.google_enabled,
        },
    }
