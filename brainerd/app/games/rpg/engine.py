"""RPG game engine — manages game state, history, and AI narration."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.games.rpg.prompts import build_system_prompt
from app.models.database import RPGGame, RPGTurn
from app.models.rpg import ActionResponse, CharacterSheet, GameInfo, NewGameRequest, TurnOut
from app.services.ai_router import complete

logger = logging.getLogger(__name__)
settings = get_settings()


async def create_game(req: NewGameRequest, db: AsyncSession) -> GameInfo:
    character = req.character.model_dump()
    character["name"] = req.player_name if character["name"] == "Adventurer" else character["name"]

    system_prompt = build_system_prompt(
        world=req.world,
        player_name=req.player_name,
        character=character,
        world_state={},
        custom_setting=req.custom_setting,
    )

    game = RPGGame(
        name=req.name,
        world=req.world,
        player_name=req.player_name,
        character=character,
        world_state={"location": "start", "quests": [], "flags": {}},
        system_prompt=system_prompt,
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    # Generate opening narration
    opening = await _narrate(game, "Begin the adventure. Set the scene for where I am and what I see.", None)
    turn = RPGTurn(
        game_id=game.id,
        role="assistant",
        content=opening["content"],
        turn_number=0,
    )
    db.add(turn)
    await db.commit()

    return _game_to_info(game, turn_count=1)


async def take_action(
    game_id: str,
    action: str,
    provider: str | None,
    db: AsyncSession,
) -> ActionResponse:
    game = await _get_game(game_id, db)
    if not game:
        raise ValueError(f"Game {game_id} not found")

    turn_count = len(game.turns)

    # Persist player action
    player_turn = RPGTurn(
        game_id=game.id,
        role="user",
        content=action,
        turn_number=turn_count,
    )
    db.add(player_turn)
    await db.flush()

    # Get AI narration
    result = await _narrate(game, action, provider)

    # Persist AI response
    ai_turn = RPGTurn(
        game_id=game.id,
        role="assistant",
        content=result["content"],
        turn_number=turn_count + 1,
    )
    db.add(ai_turn)
    await db.commit()
    await db.refresh(game)

    return ActionResponse(
        game_id=game.id,
        turn_number=turn_count + 1,
        narrative=result["content"],
        character=game.character,
        world_state=game.world_state,
        provider=result["provider"],
    )


async def get_game(game_id: str, db: AsyncSession) -> GameInfo | None:
    game = await _get_game(game_id, db)
    if not game:
        return None
    return _game_to_info(game, turn_count=len(game.turns))


async def list_games(db: AsyncSession) -> list[GameInfo]:
    result = await db.execute(
        select(RPGGame).options(selectinload(RPGGame.turns)).order_by(RPGGame.updated_at.desc())
    )
    games = result.scalars().all()
    return [_game_to_info(g, len(g.turns)) for g in games]


async def get_turns(game_id: str, db: AsyncSession) -> list[TurnOut]:
    game = await _get_game(game_id, db)
    if not game:
        return []
    return [
        TurnOut(
            id=t.id,
            role=t.role,
            content=t.content,
            turn_number=t.turn_number,
            created_at=t.created_at,
        )
        for t in game.turns
    ]


# ─── Internal helpers ─────────────────────────────────────────────────────────

async def _narrate(game: RPGGame, action: str, provider: str | None) -> dict:
    history = _build_history(game)

    messages = [
        {"role": "system", "content": game.system_prompt},
        *history,
        {"role": "user", "content": action},
    ]

    # Trim history if too long (preserve system + last N turns)
    max_hist = settings.rpg_max_history
    if len(messages) > max_hist + 2:
        messages = [messages[0]] + messages[-(max_hist):]

    return await complete(messages, provider=provider)


def _build_history(game: RPGGame) -> list[dict]:
    return [
        {"role": t.role, "content": t.content}
        for t in game.turns
    ]


async def _get_game(game_id: str, db: AsyncSession) -> RPGGame | None:
    result = await db.execute(
        select(RPGGame)
        .options(selectinload(RPGGame.turns))
        .where(RPGGame.id == game_id)
    )
    return result.scalar_one_or_none()


def _game_to_info(game: RPGGame, turn_count: int = 0) -> GameInfo:
    return GameInfo(
        id=game.id,
        name=game.name,
        world=game.world,
        player_name=game.player_name,
        character=game.character,
        world_state=game.world_state,
        turn_count=turn_count,
        created_at=game.created_at,
        updated_at=game.updated_at,
    )
