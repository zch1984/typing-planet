"""Headless GUI pipeline integration test using the SDL dummy driver.

Exercises menu -> lesson -> typing -> results -> DB persistence without a real
display, so the whole rendering path is covered in CI.
"""
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


def test_full_pipeline(dummy_env):
    import pygame
    from typingplanet.core.engine import Engine
    from typingplanet.scenes.lesson import LessonScene
    from typingplanet.scenes.menu import MainMenuScene
    from typingplanet.scenes.results import ResultsScene

    db = os.path.join(dummy_env, "t.db")
    e = Engine(db_path=db)
    e.init_pygame()
    try:
        e.push_scene(MainMenuScene(e))
        for _ in range(3):
            e._starfield.update(0.016)
            e.particles.update(0.016)
            e.current_scene.update(0.016)
            e._draw_background()
            e.current_scene.draw(e.screen)
            e.particles.draw(e.screen)
            pygame.display.flip()

        lesson = e.lessons()[0]
        e.push_scene(LessonScene(e, lesson))
        for ch in lesson.full_text:
            ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UNKNOWN,
                                    unicode=ch, mod=0)
            e.current_scene.handle_event(ev)
            e.current_scene.update(0.02)
            e.current_scene.draw(e.screen)
        assert e.current_scene.session.is_complete

        e.current_scene.update(1.0)  # force transition to results
        assert isinstance(e.current_scene, ResultsScene)
        e.current_scene.update(0.2)
        e.current_scene.draw(e.screen)

        best = e.store.attempts.best_for_lesson(e.profile.id, lesson.id)
        assert best is not None
        assert best.stars == e.current_scene.stars
    finally:
        e.store.close()
        pygame.quit()
