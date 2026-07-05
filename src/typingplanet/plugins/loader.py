"""Plugin discovery and registration.

Built-in providers/modes are registered first. External plugins can hook in via
the ``typingplanet.plugins`` entry-point group; each entry point must expose a
``register(registry: Registry) -> None`` callable.
"""
from __future__ import annotations

from importlib.metadata import entry_points

from .registry import Registry


def load_builtin(registry: Registry) -> None:
    from ..content.providers import (
        BasicTrainingProvider,
        ClassicGameMode,
        DefaultRewardStrategy,
        PinyinProvider,
    )

    registry.register_lesson_provider(BasicTrainingProvider())
    registry.register_lesson_provider(PinyinProvider())
    registry.register_game_mode(ClassicGameMode(), default=True)
    registry.register_reward_strategy(DefaultRewardStrategy(), default=True)


def discover_entry_points(registry: Registry) -> int:
    """Load third-party plugins exposing the ``typingplanet.plugins`` group.

    Returns the number of plugin modules loaded.
    """
    loaded = 0
    try:
        eps = entry_points(group="typingplanet.plugins")
    except TypeError:
        eps = entry_points().get("typingplanet.plugins", [])
    for ep in eps:
        try:
            module = ep.load()
            register = getattr(module, "register", None)
            if callable(register):
                register(registry)
                loaded += 1
        except Exception:
            continue
    return loaded


def build_registry() -> Registry:
    registry = Registry()
    load_builtin(registry)
    discover_entry_points(registry)
    return registry
