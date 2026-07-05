"""Results scene shown after completing a lesson."""
from __future__ import annotations

from typing import Optional

import pygame

from ..core.scene import Scene
from ..ui.widgets import Button, draw_stars, rounded_rect


class ResultsScene(Scene):
    def __init__(self, app, lesson, result, stars: int) -> None:
        super().__init__(app)
        self.lesson = lesson
        self.result = result
        self.stars = stars
        self._star_anim = 0.0
        self._stars_popped = 0
        self._best_stars = 0
        self._next_lesson = None
        self._btn_retry: Optional[Button] = None
        self._btn_next: Optional[Button] = None
        self._btn_menu: Optional[Button] = None

    def on_enter(self) -> None:
        t = self.app.theme
        f = self.app.assets.font(t.body_size)
        pid = self.app.profile.id if self.app.profile else ""
        prog = self.app.store.progress.get(pid, self.lesson.id)
        self._best_stars = prog.best_stars if prog else self.stars

        # next unlocked lesson within the same subject
        subject = self.app.registry.subject_lessons(self.lesson.provider_id)
        unlock = self.app.progression.unlock_state(pid, subject)
        nxt = None
        try:
            idx = subject.index(self.lesson)
        except ValueError:
            idx = -1
        if idx >= 0:
            for cand in subject[idx + 1:]:
                if unlock.get(cand.id, False):
                    nxt = cand
                    break
        self._next_lesson = nxt

        bw, bh, gap = 200, 56, 24
        total = bw * 3 + gap * 2
        start_x = (self.app.width - total) // 2
        by = self.app.height - 110
        self._btn_retry = Button((start_x, by, bw, bh), "再试一次",
                                 callback=self._retry, font=f, style="secondary")
        self._btn_next = Button((start_x + (bw + gap), by, bw, bh), "下一关",
                                callback=self._next, font=f, style="primary",
                                enabled=nxt is not None)
        self._btn_menu = Button((start_x + 2 * (bw + gap), by, bw, bh), "返回菜单",
                                callback=self._menu, font=f, style="ghost")

    def _retry(self) -> None:
        from .lesson import LessonScene
        self.app.replace_scene(LessonScene(self.app, self.lesson))

    def _next(self) -> None:
        if self._next_lesson is not None:
            from .lesson import LessonScene
            self.app.replace_scene(LessonScene(self.app, self._next_lesson))

    def _menu(self) -> None:
        from .menu import MainMenuScene
        self.app.replace_scene(MainMenuScene(self.app))

    def update(self, dt: float) -> None:
        self._star_anim = min(1.0, self._star_anim + dt / 0.9)
        target = min(self.stars, int(self._star_anim * 3))
        if self._star_anim >= 0.98:
            target = self.stars
        while self._stars_popped < target:
            self._stars_popped += 1
            self.app.play_sound("star")
        for b in (self._btn_retry, self._btn_next, self._btn_menu):
            if b is not None:
                b.update(dt)

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in (self._btn_retry, self._btn_next, self._btn_menu):
            if b is not None:
                b.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self._next_lesson is not None:
                    self._next()
                else:
                    self._menu()
            elif event.key == pygame.K_r:
                self._retry()
            elif event.key == pygame.K_ESCAPE:
                self._menu()

    def draw(self, surface: pygame.Surface) -> None:
        t = self.app.theme
        f_title = self.app.assets.font(t.title_size, bold=True)
        f_h = self.app.assets.font(t.heading_size, bold=True)
        f_body = self.app.assets.font(t.body_size)
        f_small = self.app.assets.font(t.small_size)

        title = f_title.render("完成!", True, t.text)
        surface.blit(title, title.get_rect(center=(self.app.width // 2, 130)))

        shown = min(self.stars, int(self._star_anim * 3))
        if self._star_anim >= 0.98:
            shown = self.stars
        draw_stars(surface, self.app.width // 2, 240, shown, total=3, r=34, gap=56, theme=t)

        r = self.result
        panel = pygame.Rect(0, 0, 520, 200)
        panel.center = (self.app.width // 2, 420)
        rounded_rect(surface, t.panel, panel, radius=16)
        rounded_rect(surface, t.border, panel, radius=16, width=2)

        def line(label, value, y, col):
            l = f_body.render(label, True, t.text_dim)
            v = f_h.render(value, True, col)
            surface.blit(l, (panel.x + 40, y))
            surface.blit(v, v.get_rect(topright=(panel.right - 40, y - 6)))

        line("速度", f"{int(r.wpm)} WPM", panel.y + 30, pygame.Color(t.accent2))
        line("准确率", f"{int(r.accuracy * 100)}%", panel.y + 90, pygame.Color(t.accent))
        line("用时", f"{r.duration_s:.1f} 秒", panel.y + 150, pygame.Color(t.text))

        best = f_small.render(f"最佳: {self._best_stars} 星", True, t.text_dim)
        surface.blit(best, best.get_rect(center=(self.app.width // 2, panel.bottom + 36)))

        for b in (self._btn_retry, self._btn_next, self._btn_menu):
            if b is not None:
                b.draw(surface, t)
