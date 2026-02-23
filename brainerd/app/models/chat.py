"""Pydantic request/response schemas for chat."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MessageIn(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    system_prompt: str | None = None
    provider: Literal["ollama", "google", "auto"] | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    content: str
    provider: str
    tokens: int = 0


class SessionInfo(BaseModel):
    id: str
    name: str
    source: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    provider: str
    created_at: datetime
