"""Chat API — REST + WebSocket endpoints."""

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.connection import get_db
from app.models.chat import ChatRequest, ChatResponse, MessageOut, SessionInfo
from app.models.database import ChatMessage, ChatSession
from app.services.ai_router import complete

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


# ─── REST ─────────────────────────────────────────────────────────────────────

@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message and receive a response. Creates session if not provided."""
    session = await _get_or_create_session(req.session_id, db)

    # Persist user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    await db.flush()

    # Build message history
    history = await _build_history(session.id, db)
    if req.system_prompt:
        history = [{"role": "system", "content": req.system_prompt}] + history

    # Get AI response
    result = await complete(history, provider=req.provider)

    # Persist assistant message
    ai_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result["content"],
        provider=result["provider"],
        tokens=result.get("tokens", 0),
    )
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    return ChatResponse(
        session_id=session.id,
        message_id=ai_msg.id,
        content=result["content"],
        provider=result["provider"],
        tokens=result.get("tokens", 0),
    )


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession).order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    out = []
    for s in sessions:
        count_result = await db.execute(
            select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == s.id)
        )
        count = count_result.scalar() or 0
        out.append(SessionInfo(
            id=s.id, name=s.name, source=s.source,
            created_at=s.created_at, updated_at=s.updated_at,
            message_count=count,
        ))
    return out


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    msgs = result.scalars().all()
    return [
        MessageOut(id=m.id, role=m.role, content=m.content, provider=m.provider, created_at=m.created_at)
        for m in msgs
    ]


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()


# ─── WebSocket ────────────────────────────────────────────────────────────────

@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket chat endpoint.
    Send: {"message": "...", "provider": "auto"}
    Receive: {"type": "chunk"|"done"|"error", "content": "..."}
    """
    await websocket.accept()
    session = await _get_or_create_session(session_id, db)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON"})
                continue

            message = data.get("message", "").strip()
            if not message:
                continue

            provider = data.get("provider")
            system_prompt = data.get("system_prompt")

            # Persist user message
            user_msg = ChatMessage(session_id=session.id, role="user", content=message)
            db.add(user_msg)
            await db.flush()

            # Build history
            history = await _build_history(session.id, db)
            if system_prompt:
                history = [{"role": "system", "content": system_prompt}] + history

            # Stream response
            full_content = ""
            used_provider = "ollama"
            try:
                stream_gen = await complete(history, provider=provider, stream=True)
                if hasattr(stream_gen, "__aiter__"):
                    async for chunk in stream_gen:
                        full_content += chunk
                        await websocket.send_json({"type": "chunk", "content": chunk})
                    used_provider = provider or "auto"
                else:
                    # Non-streaming fallback
                    full_content = stream_gen["content"]
                    used_provider = stream_gen["provider"]
                    await websocket.send_json({"type": "chunk", "content": full_content})
            except Exception as exc:
                logger.error("AI error in websocket: %s", exc)
                await websocket.send_json({"type": "error", "content": str(exc)})
                continue

            # Persist AI message
            ai_msg = ChatMessage(
                session_id=session.id, role="assistant",
                content=full_content, provider=used_provider,
            )
            db.add(ai_msg)
            await db.commit()

            await websocket.send_json({
                "type": "done",
                "session_id": session.id,
                "message_id": ai_msg.id,
            })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: session=%s", session_id)


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_or_create_session(session_id: str | None, db: AsyncSession) -> ChatSession:
    if session_id:
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            return session

    session = ChatSession(id=session_id or str(uuid.uuid4()))
    db.add(session)
    await db.flush()
    return session


async def _build_history(session_id: str, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    msgs = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in msgs]
