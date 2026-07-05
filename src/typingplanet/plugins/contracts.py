"""Plugin contracts.

Everything extensible in TypingPlanet is a Protocol implemented here. Third
parties can add content, game modes or reward behaviour by implementing one of
these and registering it with the ``Registry``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence, runtime_checkable

from ..domain.models import AttemptResult, Difficulty, Lesson
from ..services.typing import KeyResult, TypingSession, TypingStatistics


@runtime_checkable
class LessonProvider(Protocol):
    """Supplies a set of lessons. Content packs implement this."""

    provider_id: str
    name: str

    def lessons(self) -> Sequence[Lesson]: ...

    def get_lesson(self, lesson_id: str) -> Lesson | None: ...


@runtime_checkable
class GameMode(Protocol):
    """Defines how a lesson is played. The classic mode is plain blocking typing;
    future modes (timed, falling words, boss battle) implement this."""

    mode_id: str
    name: str
    description: str

    def build_session(self, lesson: Lesson) -> TypingSession: ...

    def is_finished(self, session: TypingSession) -> bool: ...


@dataclass(frozen=True)
class SoundEvent:
    name: str


@dataclass(frozen=True)
class BurstEvent:
    anchor: str = "cursor"  # "cursor" | "center"
    color: str = "gold"
    count: int = 12


@dataclass(frozen=True)
class TextEvent:
    text: str
    color: str = "white"


RewardEvent = SoundEvent | BurstEvent | TextEvent


@runtime_checkable
class RewardStrategy(Protocol):
    """Turns typing outcomes into discrete reward events (sounds, particle
    bursts, floating text) that the scene applies. Keeping this declarative lets
    reward rules be unit-tested without the engine."""

    strategy_id: str

    def on_key(self, result: KeyResult, stats: TypingStatistics) -> Sequence[RewardEvent]: ...

    def on_complete(self, stats: TypingStatistics, stars: int) -> Sequence[RewardEvent]: ...
