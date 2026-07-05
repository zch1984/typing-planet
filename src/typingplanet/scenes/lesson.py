"""The typing practice scene."""
from __future__ import annotations

import time
from typing import Optional

import pygame
from loguru import logger

from ..core.input import char_from_keydown
from ..core.render import render_text
from ..core.scene import Scene
from ..domain.models import AttemptResult, utcnow
from ..plugins.contracts import BurstEvent, SoundEvent, TextEvent
from ..ui.widgets import VirtualKeyboard, draw_progress, rounded_rect

TEXT_MARGIN_X = 160


def _render_block(font, text, color, line_height):
    lines = text.split("\n")
    surfs = [font.render(ln, True, color) for ln in lines]
    w = max((s.get_width() for s in surfs), default=1)
    h = len(lines) * line_height
    surf = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
    for i, s in enumerate(surfs):
        surf.blit(s, ((w - s.get_width()) // 2, i * line_height))
    return surf, (w, h)


class LessonScene(Scene):
    def __init__(self, app, lesson) -> None:
        super().__init__(app)
        self.lesson = lesson
        self.mode = app.registry.get_game_mode(None)
        self.reward = app.registry.get_reward_strategy(None)
        self.session = self.mode.build_session(lesson)
        self.keyboard = VirtualKeyboard()

        self._recorded = False
        self._complete_timer: Optional[float] = None
        self._result: Optional[AttemptResult] = None
        self._stars = 0
        self._wrong_flash = 0.0
        self._cursor_screen = (0, 0)
        self._float_texts: list[list] = []
        logger.debug("LessonScene created: {} ({} chars, display={})",
                     lesson.title, len(lesson.full_text), lesson.has_display)

    def on_enter(self) -> None:
        kb_y = self.app.height - 230
        self.keyboard.layout(TEXT_MARGIN_X, kb_y, key_w=48, key_h=48, gap=6,
                             width=self.app.width - 2 * TEXT_MARGIN_X)

    def _toggle_mute(self) -> None:
        s = self.app.settings
        s.audio.enabled = not s.audio.enabled
        self.app.audio.set_enabled(s.audio.enabled)
        s.save()
        logger.info("audio enabled={}", s.audio.enabled)

    def _color_for_burst(self, name: str):
        t = self.app.theme
        return {
            "gold": pygame.Color(t.star),
            "cyan": pygame.Color(t.accent2),
            "red": pygame.Color(t.incorrect),
            "green": pygame.Color(t.accent),
        }.get(name, pygame.Color(t.star))

    def _apply_events(self, events, anchor_pos=None) -> None:
        for ev in events:
            if isinstance(ev, SoundEvent):
                self.app.play_sound(ev.name)
            elif isinstance(ev, BurstEvent):
                if ev.anchor == "center":
                    x, y = self.app.width // 2, self.app.height // 2
                else:
                    x, y = anchor_pos or self._cursor_screen
                self.app.burst(x, y, self._color_for_burst(ev.color), ev.count)
            elif isinstance(ev, TextEvent):
                self._float_texts.append(
                    [ev.text, self.app.width // 2, self.app.height // 2 - 40,
                     1.4, 1.4, self._color_for_burst(ev.color)])

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.app.pop_scene()
            return
        if event.key == pygame.K_F1:
            self._toggle_mute()
            return
        if self.session.is_complete:
            return
        ch = char_from_keydown(event)
        logger.debug("KEYDOWN key={} unicode={!r} mod={} -> char={!r}",
                     event.key, event.unicode, event.mod, ch)
        if ch is None:
            return
        ts = time.perf_counter()
        result = self.session.input(ch, ts)
        stats = self.session.statistics()
        self._apply_events(self.reward.on_key(result, stats), self._cursor_screen)
        if result.value == "incorrect":
            self._wrong_flash = 0.25
        if self.session.is_complete and not self._recorded:
            self._finalize()

    def _finalize(self) -> None:
        self._recorded = True
        stats = self.session.statistics()
        self._stars = self.app.stars_for(stats, self.lesson.difficulty)
        result = AttemptResult(
            profile_id=self.app.profile.id if self.app.profile else "",
            lesson_id=self.lesson.id,
            wpm=stats.wpm,
            accuracy=stats.accuracy,
            correct_chars=stats.correct_chars,
            error_chars=stats.error_chars,
            duration_s=stats.duration_s,
            stars=self._stars,
            completed_at=utcnow(),
        )
        self._result = result
        provider = self.app.registry.get_lesson_provider(self.lesson.provider_id)
        subject_lessons = provider.lessons() if provider else self.app.lessons()
        self.app.progression.record_attempt(
            result.profile_id, self.lesson, result, subject_lessons)
        self._apply_events(self.reward.on_complete(stats, self._stars), self._cursor_screen)
        self._complete_timer = 0.9
        logger.info("lesson '{}' completed: wpm={:.0f} acc={:.0%} stars={}",
                    self.lesson.title, stats.wpm, stats.accuracy, self._stars)

    def update(self, dt: float) -> None:
        if self._wrong_flash > 0:
            self._wrong_flash = max(0.0, self._wrong_flash - dt)
        if self._complete_timer is not None:
            self._complete_timer -= dt
            if self._complete_timer <= 0:
                self._complete_timer = None
                from .results import ResultsScene
                self.app.replace_scene(
                    ResultsScene(self.app, self.lesson, self._result, self._stars))
        alive = []
        for ft in self._float_texts:
            ft[2] -= 30 * dt
            ft[3] -= dt
            if ft[3] > 0:
                alive.append(ft)
        self._float_texts = alive

    # ---- draw ----
    def draw(self, surface: pygame.Surface) -> None:
        t = self.app.theme
        target = self.lesson.full_text
        pos = self.session.position
        has_display = self.lesson.has_display

        if has_display:
            f_chinese = self.app.assets.font(54, bold=True)
            f_type = self.app.assets.font(40, bold=True)
        else:
            f_type = self.app.assets.font(t.typing_size, bold=True)
        line_h = int((40 if has_display else t.typing_size) * 1.5)

        colors = {
            "correct": pygame.Color(t.correct),
            "pending": pygame.Color(t.pending),
            "current": pygame.Color(t.current_fg),
        }
        max_w = self.app.width - 2 * TEXT_MARGIN_X
        text_surf, rects, size = render_text(f_type, target, pos, colors, max_w, line_h)

        area_top = 150
        area_bottom = self.app.height - 250

        if has_display:
            ch_line_h = 70
            chinese_surf, ch_size = _render_block(
                f_chinese, self.lesson.display_text, pygame.Color(t.text), ch_line_h)
            gap = 34
            total_h = ch_size[1] + gap + size[1]
            start_y = area_top + max(0, (area_bottom - area_top - total_h) // 2)
            chinese_y = start_y
            text_y = start_y + ch_size[1] + gap
            text_x = (self.app.width - size[0]) // 2
            surface.blit(chinese_surf, ((self.app.width - ch_size[0]) // 2, chinese_y))
        else:
            text_x = (self.app.width - size[0]) // 2
            text_y = area_top + max(0, (area_bottom - area_top - size[1]) // 2)

        if self._wrong_flash > 0:
            flash = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
            a = int(60 * (self._wrong_flash / 0.25))
            flash.fill((230, 57, 70, a))
            surface.blit(flash, (0, 0))

        if not self.session.is_complete and pos < len(target):
            rx, ry, cw, _lh = rects[pos]
            cx = text_x + rx
            cy = text_y + ry
            if target[pos] == "\n" or cw == 0:
                pygame.draw.rect(surface, t.current_bg,
                                 (cx, cy + 6, 4, line_h - 12), border_radius=2)
                self._cursor_screen = (cx + 6, cy + line_h // 2)
            else:
                pygame.draw.rect(surface, t.current_bg,
                                 (cx - 2, cy, cw + 4, line_h), border_radius=6)
                self._cursor_screen = (cx + cw // 2, cy + line_h // 2)

        surface.blit(text_surf, (text_x, text_y))

        self._draw_stats(surface, t)
        highlight = self.session.expected_char() if not self.session.is_complete else None
        self.keyboard.draw(surface, t, highlight=highlight,
                           font=self.app.assets.font(t.keyboard_size, bold=True))
        f_big = self.app.assets.font(t.heading_size, bold=True)
        for ft in self._float_texts:
            txt, x, y, life, mx, col = ft
            alpha = max(0, min(255, int(255 * (life / mx))))
            s = f_big.render(txt, True, col)
            s.set_alpha(alpha)
            surface.blit(s, s.get_rect(center=(int(x), int(y))))

    def _draw_stats(self, surface, t) -> None:
        f = self.app.assets.font(t.body_size)
        f_small = self.app.assets.font(t.small_size)
        bar = pygame.Rect(0, 0, self.app.width, 90)
        s = pygame.Surface((bar.w, bar.h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 90))
        surface.blit(s, bar.topleft)

        title = f.render(self.lesson.title, True, t.text)
        surface.blit(title, (TEXT_MARGIN_X, 24))

        stats = self.session.statistics()
        wpm_txt = f.render(f"{int(stats.wpm)} WPM", True, t.accent2)
        surface.blit(wpm_txt, wpm_txt.get_rect(topright=(self.app.width - TEXT_MARGIN_X, 22)))
        acc_txt = f_small.render(f"准确率 {int(stats.accuracy * 100)}%", True, t.text)
        surface.blit(acc_txt, acc_txt.get_rect(topright=(self.app.width - TEXT_MARGIN_X, 56)))

        total = len(self.lesson.full_text)
        frac = self.session.position / total if total else 0
        prog = pygame.Rect(TEXT_MARGIN_X, 64, self.app.width - 2 * TEXT_MARGIN_X - 200, 12)
        prog.center = (prog.centerx, 70)
        draw_progress(surface, prog, frac, t)
        hint = f_small.render("Esc 返回    F1 静音", True, t.text_dim)
        surface.blit(hint, (TEXT_MARGIN_X, 92))
