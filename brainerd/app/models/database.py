"""SQLAlchemy ORM models stored in SQLite."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ─── Chat ────────────────────────────────────────────────────────────────────

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, default="New Chat")
    source: Mapped[str] = mapped_column(String, default="api")  # api | websocket | container
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String)        # user | assistant | system
    content: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String, default="ollama")  # ollama | google
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


# ─── RPG ─────────────────────────────────────────────────────────────────────

class RPGGame(Base):
    __tablename__ = "rpg_games"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String)
    world: Mapped[str] = mapped_column(String, default="fantasy")
    player_name: Mapped[str] = mapped_column(String, default="Adventurer")
    character: Mapped[dict] = mapped_column(JSON, default=dict)   # stats, inventory, etc.
    world_state: Mapped[dict] = mapped_column(JSON, default=dict) # flags, location, quests
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    turns: Mapped[list["RPGTurn"]] = relationship(
        back_populates="game", cascade="all, delete-orphan", order_by="RPGTurn.created_at"
    )


class RPGTurn(Base):
    __tablename__ = "rpg_turns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    game_id: Mapped[str] = mapped_column(ForeignKey("rpg_games.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String)      # user | assistant
    content: Mapped[str] = mapped_column(Text)
    turn_number: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    game: Mapped["RPGGame"] = relationship(back_populates="turns")
