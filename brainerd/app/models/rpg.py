"""Pydantic schemas for RPG game engine."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CharacterSheet(BaseModel):
    name: str = "Adventurer"
    race: str = "Human"
    char_class: str = "Fighter"
    level: int = 1
    hp: int = 20
    max_hp: int = 20
    stats: dict[str, int] = Field(
        default_factory=lambda: {
            "strength": 10, "dexterity": 10, "constitution": 10,
            "intelligence": 10, "wisdom": 10, "charisma": 10,
        }
    )
    inventory: list[str] = Field(default_factory=list)
    gold: int = 10
    experience: int = 0


class NewGameRequest(BaseModel):
    name: str = "My Adventure"
    world: Literal["fantasy", "sci-fi", "horror", "western", "custom"] = "fantasy"
    player_name: str = "Adventurer"
    character: CharacterSheet = Field(default_factory=CharacterSheet)
    custom_setting: str | None = None  # free-text world description for "custom"


class ActionRequest(BaseModel):
    game_id: str
    action: str
    provider: Literal["ollama", "google", "auto"] | None = None


class TurnOut(BaseModel):
    id: str
    role: str
    content: str
    turn_number: int
    created_at: datetime


class GameInfo(BaseModel):
    id: str
    name: str
    world: str
    player_name: str
    character: dict[str, Any]
    world_state: dict[str, Any]
    turn_count: int = 0
    created_at: datetime
    updated_at: datetime


class ActionResponse(BaseModel):
    game_id: str
    turn_number: int
    narrative: str
    character: dict[str, Any]
    world_state: dict[str, Any]
    provider: str
