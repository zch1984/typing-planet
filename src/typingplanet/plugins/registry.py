"""Central registry for all extensible components."""
from __future__ import annotations

from ..domain.models import Lesson
from .contracts import GameMode, LessonProvider, RewardStrategy


class Registry:
    def __init__(self) -> None:
        self._lesson_providers: dict[str, LessonProvider] = {}
        self._game_modes: dict[str, GameMode] = {}
        self._reward_strategies: dict[str, RewardStrategy] = {}
        self._default_mode_id: str = ""
        self._default_reward_id: str = ""

    # ---- lesson providers (subjects) ----
    def register_lesson_provider(self, provider: LessonProvider) -> None:
        self._lesson_providers[provider.provider_id] = provider

    def lesson_providers(self) -> list[LessonProvider]:
        return list(self._lesson_providers.values())

    def get_lesson_provider(self, provider_id: str) -> LessonProvider | None:
        return self._lesson_providers.get(provider_id)

    def subject_lessons(self, provider_id: str) -> list[Lesson]:
        """Lessons of one subject (provider), sorted by order then id."""
        provider = self._lesson_providers.get(provider_id)
        if provider is None:
            return []
        lessons = list(provider.lessons())
        lessons.sort(key=lambda l: (l.order, l.id))
        return lessons

    def all_lessons(self) -> list[Lesson]:
        lessons: list[Lesson] = []
        for provider in self._lesson_providers.values():
            lessons.extend(provider.lessons())
        lessons.sort(key=lambda l: (l.order, l.id))
        return lessons

    def get_lesson(self, lesson_id: str) -> Lesson | None:
        for provider in self._lesson_providers.values():
            lesson = provider.get_lesson(lesson_id)
            if lesson is not None:
                return lesson
        return None

    # ---- game modes ----
    def register_game_mode(self, mode: GameMode, *, default: bool = False) -> None:
        self._game_modes[mode.mode_id] = mode
        if default or not self._default_mode_id:
            self._default_mode_id = mode.mode_id

    def game_modes(self) -> list[GameMode]:
        return list(self._game_modes.values())

    def get_game_mode(self, mode_id: str | None) -> GameMode | None:
        if not mode_id:
            return self._game_modes.get(self._default_mode_id)
        return self._game_modes.get(mode_id)

    # ---- reward strategies ----
    def register_reward_strategy(self, strategy: RewardStrategy, *, default: bool = False) -> None:
        self._reward_strategies[strategy.strategy_id] = strategy
        if default or not self._default_reward_id:
            self._default_reward_id = strategy.strategy_id

    def reward_strategies(self) -> list[RewardStrategy]:
        return list(self._reward_strategies.values())

    def get_reward_strategy(self, strategy_id: str | None) -> RewardStrategy | None:
        if not strategy_id:
            return self._reward_strategies.get(self._default_reward_id)
        return self._reward_strategies.get(strategy_id)
