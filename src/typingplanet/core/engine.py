"""The game engine: window, main loop, scene stack and shared services."""
from __future__ import annotations

from typing import Optional

import pygame
from loguru import logger

from ..config.paths import config_dir, data_dir, db_path, log_path
from ..config.settings import GameSettings
from ..data.sqlite_repositories import DataStore
from ..domain.models import Difficulty, Profile
from ..plugins.loader import build_registry
from ..plugins.registry import Registry
from ..services.progression import ProgressionService
from ..services.scoring import compute_stars
from .assets import AssetManager
from .audio import AudioManager
from .background import Starfield
from .particles import ParticleSystem
from .scene import Scene
from .theme import Theme, default_theme


class Engine:
    def __init__(self, settings: Optional[GameSettings] = None, db_path=None) -> None:
        self.settings = settings or GameSettings.load()
        self.theme: Theme = default_theme()
        self.assets = AssetManager()
        self.audio = AudioManager(
            enabled=self.settings.audio.enabled, volume=self.settings.audio.volume
        )
        self.particles = ParticleSystem()
        self.registry: Registry = build_registry()
        self.store = DataStore.open(db_path)
        self.progression = ProgressionService(self.store.progress, self.store.attempts)

        self._scene_stack: list[Scene] = []
        self._running = False
        self._screen: Optional[pygame.Surface] = None
        self._clock: Optional[pygame.time.Clock] = None
        self._starfield: Optional[Starfield] = None
        self._bg: Optional[pygame.Surface] = None

        self.profile: Optional[Profile] = None
        self._ensure_profile()

    # ---- setup ----
    def _ensure_profile(self) -> None:
        profiles = self.store.profiles.list_all()
        if profiles:
            if self.settings.active_profile_id:
                for p in profiles:
                    if p.id == self.settings.active_profile_id:
                        self.profile = p
                        return
            self.profile = profiles[0]
            self.settings.active_profile_id = self.profile.id
            self.settings.save()
        else:
            self.profile = self.store.profiles.create("玩家1")
            self.settings.active_profile_id = self.profile.id
            self.settings.save()

    def init_pygame(self) -> None:
        pygame.init()
        flags = pygame.SCALED
        if self.settings.window.fullscreen:
            flags |= pygame.FULLSCREEN
        self._screen = pygame.display.set_mode(
            (self.settings.window.width, self.settings.window.height), flags, vsync=1
        )
        pygame.display.set_caption("TypingPlanet 打字星球")
        # Discourage the system IME from composing on key presses; the keycode
        # fallback in core.input still handles the case where it does.
        try:
            pygame.key.stop_text_input()
        except Exception:
            pass
        self.audio.init()
        self._clock = pygame.time.Clock()
        self._starfield = Starfield(self.settings.window.width, self.settings.window.height)
        self._bg = self._build_gradient()

    def _build_gradient(self) -> pygame.Surface:
        w, h = self.settings.window.width, self.settings.window.height
        top = pygame.Color(self.theme.bg_top)
        bot = pygame.Color(self.theme.bg_bottom)
        surf = pygame.Surface((w, h)).convert()
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(top.r + (bot.r - top.r) * t)
            g = int(top.g + (bot.g - top.g) * t)
            b = int(top.b + (bot.b - top.b) * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
        return surf

    # ---- accessors ----
    @property
    def screen(self) -> pygame.Surface:
        assert self._screen is not None, "engine not initialised"
        return self._screen

    @property
    def width(self) -> int:
        return self.settings.window.width

    @property
    def height(self) -> int:
        return self.settings.window.height

    def lessons(self):
        return self.registry.all_lessons()

    def play_sound(self, name: str) -> None:
        self.audio.play(name)

    def burst(self, x: float, y: float, color, count: int = 14) -> None:
        self.particles.burst(x, y, color, count)

    def stars_for(self, stats, difficulty: Difficulty) -> int:
        return compute_stars(stats.accuracy, stats.wpm, difficulty)

    # ---- scene management ----
    def push_scene(self, scene: Scene) -> None:
        if self._scene_stack:
            self._scene_stack[-1].on_exit()
        self._scene_stack.append(scene)
        logger.debug("push scene: {}", type(scene).__name__)
        scene.on_enter()

    def pop_scene(self) -> Optional[Scene]:
        if not self._scene_stack:
            return None
        scene = self._scene_stack.pop()
        logger.debug("pop scene: {}", type(scene).__name__)
        scene.on_exit()
        if self._scene_stack:
            self._scene_stack[-1].on_enter()
        return scene

    def replace_scene(self, scene: Scene) -> None:
        if self._scene_stack:
            self._scene_stack[-1].on_exit()
            self._scene_stack[-1] = scene
        else:
            self._scene_stack.append(scene)
        logger.debug("replace scene: {}", type(scene).__name__)
        scene.on_enter()

    @property
    def current_scene(self) -> Optional[Scene]:
        return self._scene_stack[-1] if self._scene_stack else None

    def quit(self) -> None:
        self._running = False

    # ---- main loop ----
    def run(self) -> None:
        self.init_pygame()
        logger.info("TypingPlanet starting")
        logger.info("data dir : {}", data_dir())
        logger.info("config   : {}", config_dir())
        logger.info("db       : {}", db_path())
        logger.info("log file : {}", log_path())
        logger.info("profile  : {}", self.profile.name if self.profile else None)
        logger.info("lessons  : {}", len(self.lessons()))
        logger.info("window   : {}x{} @{}fps",
                    self.width, self.height, self.settings.window.fps)

        from ..scenes.menu import MainMenuScene
        self.push_scene(MainMenuScene(self))
        self._running = True
        while self._running:
            dt = self._clock.tick(self.settings.window.fps) / 1000.0
            dt = min(dt, 1 / 30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break
                scene = self.current_scene
                if scene is not None:
                    scene.handle_event(event)

            self._starfield.update(dt)
            self.particles.update(dt)
            scene = self.current_scene
            if scene is not None:
                scene.update(dt)

            self._draw_background()
            scene = self.current_scene
            if scene is not None:
                scene.draw(self._screen)
            self.particles.draw(self._screen)
            pygame.display.flip()

        self.settings.save()
        self.store.close()
        pygame.quit()
        logger.info("TypingPlanet stopped")

    def _draw_background(self) -> None:
        if self._bg is not None:
            self._screen.blit(self._bg, (0, 0))
        if self._starfield is not None:
            self._starfield.draw(self._screen)
