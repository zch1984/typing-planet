"""Application settings, validated with pydantic and persisted as JSON."""
from __future__ import annotations

import json
from typing import Optional

from pydantic import BaseModel, Field

from .paths import settings_path


class WindowSettings(BaseModel):
    width: int = 1280
    height: int = 800
    fps: int = 60
    fullscreen: bool = False


class AudioSettings(BaseModel):
    enabled: bool = True
    volume: float = 0.7


class GameSettings(BaseModel):
    window: WindowSettings = Field(default_factory=WindowSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    theme_id: str = "space"
    active_profile_id: Optional[str] = None

    @classmethod
    def load(cls) -> "GameSettings":
        path = settings_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return cls.model_validate(data)
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        path = settings_path()
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
