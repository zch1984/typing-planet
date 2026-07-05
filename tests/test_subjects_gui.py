"""GUI integration tests for subject switching and the pinyin lesson flow."""
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
    km.update({" ": pygame.K_SPACE, "\n": pygame.K_RETURN})
    return km


def _keydown(key, mod=0):
    import pygame
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode="", mod=mod)


def test_menu_switches_between_subjects(dummy_env):
    import pygame
    from typingplanet.core.engine import Engine
    from typingplanet.scenes.menu import MainMenuScene

    e = Engine(db_path=os.path.join(dummy_env, "t.db"))
    e.init_pygame()
    try:
        m = MainMenuScene(e)
        e.push_scene(m)
        assert m._subjects and len(m._subjects) >= 2
        assert all(l.provider_id == "basic" for l in m._lessons)

        m.handle_event(_keydown(pygame.K_RIGHT))  # -> pinyin
        assert all(l.provider_id == "pinyin" for l in m._lessons)
        assert len(m._lessons) >= 5
        e._draw_background()
        m.draw(e.screen)
        pygame.display.flip()

        m.handle_event(_keydown(pygame.K_LEFT))  # back to basic
        assert all(l.provider_id == "basic" for l in m._lessons)
    finally:
        e.store.close()
        pygame.quit()


def test_pinyin_lesson_shows_chinese_and_completes(dummy_env):
    import pygame
    from typingplanet.core.engine import Engine
    from typingplanet.scenes.lesson import LessonScene
    from typingplanet.scenes.results import ResultsScene

    e = Engine(db_path=os.path.join(dummy_env, "t.db"))
    e.init_pygame()
    try:
        lesson = e.registry.subject_lessons("pinyin")[0]
        assert lesson.has_display
        assert "天" in lesson.display_text
        scene = LessonScene(e, lesson)
        e.push_scene(scene)

        # exercise the display-header draw path (no crash)
        for _ in range(3):
            e._draw_background()
            scene.draw(e.screen)
            pygame.display.flip()

        km = _keymap()
        for ch in lesson.full_text:  # "tian di ren"
            scene.handle_event(_keydown(km.get(ch, pygame.K_UNKNOWN)))
            scene.update(0.02)
        assert scene.session.is_complete

        scene.update(1.0)  # transition to results
        assert isinstance(e.current_scene, ResultsScene)
        assert e.current_scene.stars >= 0
    finally:
        e.store.close()
        pygame.quit()
