"""Domain models for TypingPlanet.

Pure data objects with no dependency on the game engine or storage layer, so
they can be reused by services, repositories and tests alike.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid.uuid4().hex


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class Profile:
    """A player profile. The game is single-player but supports multiple kids
    sharing one machine, each with their own progress."""

    id: str = field(default_factory=new_id)
    name: str = ""
    avatar: str = "default"
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class Segment:
    """A single chunk of a lesson.

    ``text`` is what the player must type. ``display`` is optional reference
    text shown above the typeable line -- used for pinyin lessons where the
    Chinese characters are shown and the player types their pinyin.
    """

    text: str
    display: str = ""
    hint: str = ""


@dataclass(frozen=True)
class Lesson:
    """A lesson is an ordered, immutable description of what to type."""

    id: str
    provider_id: str
    title: str
    description: str = ""
    difficulty: Difficulty = Difficulty.EASY
    segments: tuple[Segment, ...] = ()
    order: int = 0
    tags: tuple[str, ...] = ()

    @property
    def full_text(self) -> str:
        return "\n".join(s.text for s in self.segments)

    @property
    def display_text(self) -> str:
        return "\n".join(s.display for s in self.segments if s.display)

    @property
    def has_display(self) -> bool:
        return any(s.display for s in self.segments)


@dataclass(frozen=True)
class AttemptResult:
    """The outcome of one completed attempt at a lesson."""

    id: str = field(default_factory=new_id)
    profile_id: str = ""
    lesson_id: str = ""
    wpm: float = 0.0
    accuracy: float = 0.0  # 0..1
    correct_chars: int = 0
    error_chars: int = 0
    duration_s: float = 0.0
    stars: int = 0  # 0..3
    completed_at: datetime = field(default_factory=utcnow)


@dataclass
class LessonProgress:
    """Aggregated best-of progress for a profile on a lesson."""

    profile_id: str
    lesson_id: str
    best_wpm: float = 0.0
    best_accuracy: float = 0.0
    best_stars: int = 0
    attempts: int = 0
    last_played_at: Optional[datetime] = None
    unlocked: bool = False


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    description: str = ""
    icon: str = "star"


@dataclass(frozen=True)
class UnlockedAchievement:
    achievement_id: str
    profile_id: str
    unlocked_at: datetime = field(default_factory=utcnow)
