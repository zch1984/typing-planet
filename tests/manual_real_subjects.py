"""Manual smoke: real window showing subject tabs and a pinyin lesson header.

Run directly:  python tests/manual_real_subjects.py
Not collected by pytest.
"""
import os
import tempfile


def main() -> None:
    import pygame
    from typingplanet.core.engine import Engine
    from typingplanet.scenes.lesson import LessonScene
    from typingplanet.scenes.menu import MainMenuScene

    tmp = tempfile.mkdtemp()
    os.environ.setdefault("TYPINGPLANET_DATA_DIR", tmp)
    os.environ.setdefault("TYPINGPLANET_CONFIG_DIR", tmp)

    e = Engine(db_path=os.path.join(tmp, "t.db"))
    e.init_pygame()
    e.push_scene(MainMenuScene(e))
    clock = pygame.time.Clock()
    for _ in range(30):
        dt = clock.tick(60) / 1000.0
        if any(ev.type == pygame.QUIT for ev in pygame.event.get()):
            break
        e._starfield.update(dt)
        e.particles.update(dt)
        e.current_scene.update(dt)
        e._draw_background()
        e.current_scene.draw(e.screen)
        e.particles.draw(e.screen)
        pygame.display.flip()

    lesson = e.registry.subject_lessons("pinyin")[0]
    e.push_scene(LessonScene(e, lesson))
    for _ in range(30):
        dt = clock.tick(60) / 1000.0
        e.current_scene.update(dt)
        e._draw_background()
        e.current_scene.draw(e.screen)
        pygame.display.flip()

    e.store.close()
    pygame.quit()
    print("REAL SUBJECTS SMOKE OK")


if __name__ == "__main__":
    main()
