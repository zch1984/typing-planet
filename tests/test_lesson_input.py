"""Integration test for lesson input, simulating an active IME (empty unicode)."""
import os
import tempfile

import pytest


@pytest.fixture
def dummy_env(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    tmp = tempfile.mkdtemp()
    monkeypatch.setenv("TYPINGPLANET_DATA_DIR", tmp)
    monkeypatch.setenv("TYPINGPLANET_CONFIG_DIR", tmp)
    return tmp


def _keymap():
    import pygame
    km = {}
    for ch in "abcdefghijklmnopqrstuvwxyz":
        km[ch] = getattr(pygame, "K_" + ch)
    for ch in "0123456789":
        km[ch] = getattr(pygame, "K_" + ch)
    km.update({
        " ": pygame.K_SPACE, "\n": pygame.K_RETURN,
        ";": pygame.K_SEMICOLON, ",": pygame.K_COMMA, ".": pygame.K_PERIOD,
        "/": pygame.K_SLASH, "'": pygame.K_QUOTE, "[": pygame.K_LEFTBRACKET,
        "]": pygame.K_RIGHTBRACKET, "-": pygame.K_MINUS, "=": pygame.K_EQUALS,
    })
    return km


def test_wrong_key_does_not_advance_ime_mode(dummy_env):
    import pygame
    from typingplanet.core.engine import Engine
    from typingplanet.scenes.lesson import LessonScene

    e = Engine(db_path=os.path.join(dummy_env, "t.db"))
    e.init_pygame()
    try:
        lesson = e.registry.subject_lessons("basic")[0]  # target starts with f
        scene = LessonScene(e, lesson)
        e.push_scene(scene)
        km = _keymap()
        # wrong key (x) with empty unicode -> incorrect, no advance
        ev = pygame.event.Event(pygame.KEYDOWN, key=km["x"], unicode="", mod=0)
        scene.handle_event(ev)
        assert scene.session.position == 0
        assert scene.session.error_count == 1
    finally:
        e.store.close()
        pygame.quit()


def test_completes_with_empty_unicode_ime_mode(dummy_env):
    import pygame
    from typingplanet.core.engine import Engine
    from typingplanet.scenes.lesson import LessonScene

    e = Engine(db_path=os.path.join(dummy_env, "t.db"))
    e.init_pygame()
    try:
        lesson = e.registry.subject_lessons("basic")[0]
        scene = LessonScene(e, lesson)
        e.push_scene(scene)
        km = _keymap()
        for ch in lesson.full_text:
            key = km.get(ch, pygame.K_UNKNOWN)
            ev = pygame.event.Event(pygame.KEYDOWN, key=key, unicode="", mod=0)
            scene.handle_event(ev)
        assert scene.session.is_complete
        assert scene.session.error_count == 0
    finally:
        e.store.close()
        pygame.quit()
