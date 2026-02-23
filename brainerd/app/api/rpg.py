"""RPG game API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.games.rpg import engine
from app.models.rpg import ActionRequest, ActionResponse, GameInfo, NewGameRequest, TurnOut

router = APIRouter(prefix="/rpg", tags=["rpg"])


@router.post("/games", response_model=GameInfo, status_code=201)
async def new_game(req: NewGameRequest, db: AsyncSession = Depends(get_db)):
    """Create a new RPG game and receive the opening narration."""
    return await engine.create_game(req, db)


@router.get("/games", response_model=list[GameInfo])
async def list_games(db: AsyncSession = Depends(get_db)):
    return await engine.list_games(db)


@router.get("/games/{game_id}", response_model=GameInfo)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    game = await engine.get_game(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("/games/{game_id}/turns", response_model=list[TurnOut])
async def get_turns(game_id: str, db: AsyncSession = Depends(get_db)):
    return await engine.get_turns(game_id, db)


@router.post("/games/{game_id}/action", response_model=ActionResponse)
async def take_action(game_id: str, req: ActionRequest, db: AsyncSession = Depends(get_db)):
    """Take an action in the game and receive the GM's narration."""
    try:
        return await engine.take_action(game_id, req.action, req.provider, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
