"""Main menu: subject tabs, profile switching and lesson selection."""
from __future__ import annotations

from typing import Optional

import pygame

from ..core.scene import Scene
from ..domain.models import Difficulty
from ..ui.widgets import Button, draw_stars, rounded_rect

DIFFICULTY_LABEL = {
    Difficulty.EASY: "简单",
    Difficulty.MEDIUM: "中等",
    Difficulty.HARD: "困难",
}
DIFFICULTY_COLOR = {
    Difficulty.EASY: "#4ecca3",
    Difficulty.MEDIUM: "#ffd166",
    Difficulty.HARD: "#e63946",
}

MARGIN_X = 120
CARD_H = 66
CARD_GAP = 10
LIST_TOP = 150
TAB_Y = 80
TAB_H = 40


def draw_lock(surface: pygame.Surface, cx: int, cy: int, color, size: int = 16) -> None:
    body = pygame.Rect(0, 0, int(size * 1.1), int(size * 0.8))
    body.center = (cx, cy + size // 4)
    pygame.draw.rect(surface, color, body, border_radius=3)
    pygame.draw.arc(surface, color,
                    pygame.Rect(cx - size // 2, cy - size // 2, size, size),
                    0.4, 2.7, 3)


class MainMenuScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._subjects: list = []
        self._subject_index = 0
        self._tab_rects: list[tuple] = []
        self._lessons: list = []
        self._unlock_state: dict[str, bool] = {}
        self._best_stars: dict[str, int] = {}
        self._cards: list[pygame.Rect] = []
        self._selected = 0
        self._scroll = 0
        self._prev_btn: Optional[Button] = None
        self._next_btn: Optional[Button] = None
        self._add_btn: Optional[Button] = None
        self._mute_btn: Optional[Button] = None

    def on_enter(self) -> None:
        f = self.app.assets.font(self.app.theme.body_size)
        small = self.app.assets.font(self.app.theme.small_size)
        top = 28
        self._add_btn = Button((self.app.width - 150, top, 44, 44), "+",
                               callback=self._add_profile, font=f, style="primary")
        self._next_btn = Button((self.app.width - 204, top, 44, 44), ">",
                                callback=self._next_profile, font=f, style="secondary")
        self._prev_btn = Button((self.app.width - 360, top, 44, 44), "<",
                                callback=self._prev_profile, font=f, style="secondary")
        self._mute_btn = Button((self.app.width - 258, top, 44, 44), "",
                                callback=self._toggle_mute, font=small, style="ghost")
        self._refresh()

    # ---- data ----
    def _refresh(self) -> None:
        self._subjects = self.app.registry.lesson_providers()
        if self._subject_index >= len(self._subjects):
            self._subject_index = 0
        self._layout_tabs()
        self._load_subject()

    def _layout_tabs(self) -> None:
        f = self.app.assets.font(self.app.theme.body_size, bold=True)
        x = MARGIN_X
        self._tab_rects = []
        for provider in self._subjects:
            w = f.size(provider.name)[0] + 44
            self._tab_rects.append((provider, pygame.Rect(x, TAB_Y, w, TAB_H)))
            x += w + 12

    def _load_subject(self) -> None:
        if not self._subjects:
            self._lessons = []
            return
        provider = self._subjects[self._subject_index]
        self._lessons = self.app.registry.subject_lessons(provider.provider_id)
        pid = self.app.profile.id if self.app.profile else ""
        self._unlock_state = self.app.progression.unlock_state(pid, self._lessons)
        self._best_stars = {}
        for l in self._lessons:
            prog = self.app.store.progress.get(pid, l.id)
            self._best_stars[l.id] = prog.best_stars if prog else 0
        self._layout_cards()
        if self._selected >= len(self._lessons):
            self._selected = max(0, len(self._lessons) - 1)
        self._scroll = 0

    def _layout_cards(self) -> None:
        self._cards = []
        for i in range(len(self._lessons)):
            self._cards.append(pygame.Rect(
                MARGIN_X, LIST_TOP + i * (CARD_H + CARD_GAP),
                self.app.width - 2 * MARGIN_X, CARD_H))

    @property
    def _visible_height(self) -> int:
        return self.app.height - LIST_TOP - 60

    @property
    def _total_height(self) -> int:
        return len(self._cards) * (CARD_H + CARD_GAP)

    @property
    def _max_scroll(self) -> int:
        return max(0, self._total_height - self._visible_height)

    def _clamp_scroll(self) -> None:
        self._scroll = max(0, min(self._max_scroll, self._scroll))

    def _scroll_to_selected(self) -> None:
        if not self._cards:
            return
        r = self._cards[self._selected]
        top = r.y - self._scroll
        bottom = r.bottom - self._scroll
        if top < LIST_TOP:
            self._scroll -= (LIST_TOP - top)
        elif bottom > LIST_TOP + self._visible_height:
            self._scroll += (bottom - (LIST_TOP + self._visible_height))
        self._clamp_scroll()

    def _switch_subject(self, delta: int) -> None:
        if not self._subjects:
            return
        self._subject_index = (self._subject_index + delta) % len(self._subjects)
        self._selected = 0
        self._load_subject()

    # ---- profile actions ----
    def _add_profile(self) -> None:
        n = len(self.app.store.profiles.list_all()) + 1
        self.app.profile = self.app.store.profiles.create(f"玩家{n}")
        self.app.settings.active_profile_id = self.app.profile.id
        self.app.settings.save()
        self._load_subject()

    def _cycle_profile(self, delta: int) -> None:
        profiles = self.app.store.profiles.list_all()
        if not profiles:
            return
        ids = [p.id for p in profiles]
        cur = self.app.profile.id if self.app.profile else ids[0]
        try:
            idx = ids.index(cur)
        except ValueError:
            idx = 0
        self.app.profile = profiles[(idx + delta) % len(ids)]
        self.app.settings.active_profile_id = self.app.profile.id
        self.app.settings.save()
        self._load_subject()

    def _prev_profile(self) -> None:
        self._cycle_profile(-1)

    def _next_profile(self) -> None:
        self._cycle_profile(1)

    def _toggle_mute(self) -> None:
        s = self.app.settings
        s.audio.enabled = not s.audio.enabled
        self.app.audio.set_enabled(s.audio.enabled)
        s.save()

    def _start_selected(self) -> None:
        if not self._lessons:
            return
        lesson = self._lessons[self._selected]
        if not self._unlock_state.get(lesson.id, False):
            self.app.play_sound("key_wrong")
            return
        from .lesson import LessonScene
        self.app.push_scene(LessonScene(self.app, lesson))

    # ---- events ----
    def handle_event(self, event: pygame.event.Event) -> None:
        for b in (self._prev_btn, self._next_btn, self._add_btn, self._mute_btn):
            if b is not None:
                b.handle_event(event)

        if event.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self._cards):
                if r.move(0, -self._scroll).collidepoint(event.pos):
                    self._selected = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, (_provider, r) in enumerate(self._tab_rects):
                if r.collidepoint(event.pos):
                    self._subject_index = i
                    self._selected = 0
                    self._load_subject()
                    return
            for i, r in enumerate(self._cards):
                if r.move(0, -self._scroll).collidepoint(event.pos):
                    self._selected = i
                    self._start_selected()
                    return
        elif event.type == pygame.MOUSEWHEEL:
            self._scroll -= event.y * 60
            self._clamp_scroll()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._switch_subject(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._switch_subject(1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._selected = min(len(self._lessons) - 1, self._selected + 1)
                self._scroll_to_selected()
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._selected = max(0, self._selected - 1)
                self._scroll_to_selected()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_selected()
            elif event.key == pygame.K_m:
                self._toggle_mute()
            elif event.key == pygame.K_ESCAPE:
                self.app.quit()

    def update(self, dt: float) -> None:
        for b in (self._prev_btn, self._next_btn, self._add_btn, self._mute_btn):
            if b is not None:
                b.update(dt)

    # ---- draw ----
    def draw(self, surface: pygame.Surface) -> None:
        t = self.app.theme
        f_title = self.app.assets.font(t.title_size, bold=True)
        f_body = self.app.assets.font(t.body_size)
        f_body_b = self.app.assets.font(t.body_size, bold=True)
        f_small = self.app.assets.font(t.small_size)

        title = f_title.render("TypingPlanet  打字星球", True, t.text)
        surface.blit(title, (MARGIN_X, 24))

        pname = self.app.profile.name if self.app.profile else "—"
        ptxt = f_body.render(pname, True, t.text)
        surface.blit(ptxt, ptxt.get_rect(midright=(self.app.width - 410, 50)))
        for b in (self._prev_btn, self._next_btn, self._add_btn):
            if b is not None:
                b.draw(surface, t)
        if self._mute_btn is not None:
            self._mute_btn.label = "音效开" if self.app.settings.audio.enabled else "音效关"
            self._mute_btn.draw(surface, t)

        self._draw_tabs(surface, t, f_body_b)

        # lesson list (clipped)
        clip = pygame.Rect(0, LIST_TOP, self.app.width, self._visible_height)
        prev_clip = surface.get_clip()
        surface.set_clip(clip)
        for i, lesson in enumerate(self._lessons):
            r = self._cards[i].move(0, -self._scroll)
            if r.bottom < LIST_TOP or r.y > LIST_TOP + self._visible_height:
                continue
            self._draw_card(surface, r, lesson, i, t, f_body, f_small)
        surface.set_clip(prev_clip)

        hint = f_small.render(
            "左右 切换主题    上下 选择    Enter 开始    M 静音    Esc 退出    滚轮滚动",
            True, t.text_dim)
        surface.blit(hint, hint.get_rect(midbottom=(self.app.width // 2, self.app.height - 16)))

    def _draw_tabs(self, surface, t, f_body_b) -> None:
        for i, (provider, r) in enumerate(self._tab_rects):
            active = (i == self._subject_index)
            bg = t.accent if active else t.panel
            rounded_rect(surface, bg, r, radius=10)
            border = t.accent if active else t.border
            rounded_rect(surface, border, r, radius=10, width=2)
            col = t.current_fg if active else t.text
            label = f_body_b.render(provider.name, True, col)
            surface.blit(label, label.get_rect(center=r.center))

    def _draw_card(self, surface, r, lesson, i, t, f_body, f_small) -> None:
        unlocked = self._unlock_state.get(lesson.id, False)
        selected = (i == self._selected)
        bg = t.highlight if selected else t.panel
        rounded_rect(surface, bg, r, radius=12)
        border = t.accent if selected else t.border
        rounded_rect(surface, border, r, radius=12, width=2)

        num = f_body.render(f"{i + 1:02d}", True, t.text_dim)
        surface.blit(num, num.get_rect(midleft=(r.x + 24, r.centery)))

        title = f_body.render(lesson.title, True, t.text)
        surface.blit(title, title.get_rect(midleft=(r.x + 80, r.centery - 12)))
        dcol = pygame.Color(DIFFICULTY_COLOR[lesson.difficulty])
        dtag = f_small.render(DIFFICULTY_LABEL[lesson.difficulty], True, dcol)
        surface.blit(dtag, dtag.get_rect(midleft=(r.x + 80, r.centery + 14)))

        if unlocked:
            draw_stars(surface, r.right - 70, r.centery,
                       self._best_stars.get(lesson.id, 0), total=3, r=13, gap=22, theme=t)
        else:
            draw_lock(surface, r.right - 70, r.centery, pygame.Color(t.lock), size=18)
            lk = f_small.render("未解锁", True, t.lock)
            surface.blit(lk, lk.get_rect(midright=(r.right - 100, r.centery)))
