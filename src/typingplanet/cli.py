"""Command-line entry point."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from .config.paths import log_path
from .config.settings import GameSettings
from .core.engine import Engine

app = typer.Typer(add_completion=False, help="TypingPlanet 打字星球 - 儿童打字练习游戏")


def _setup_logging(debug: bool = False) -> None:
    logger.remove()
    level = "DEBUG" if debug else "INFO"
    try:
        logger.add(str(log_path()), level=level, rotation="2 MB", retention=5,
                   encoding="utf-8")
    except Exception:
        pass
    if sys.stderr is not None:
        logger.add(sys.stderr, level=level)


@app.callback(invoke_without_command=True)
def main(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="按名称选择用户档案"),
    db: Optional[Path] = typer.Option(None, "--db", help="自定义数据库路径（测试用）"),
    fullscreen: bool = typer.Option(False, "--fullscreen", "-f", help="全屏启动"),
    width: int = typer.Option(1280, "--width", help="窗口宽度"),
    height: int = typer.Option(800, "--height", help="窗口高度"),
    fps: int = typer.Option(60, "--fps", help="目标帧率"),
    debug: bool = typer.Option(False, "--debug", help="详细日志（含每次按键）"),
) -> None:
    """启动打字星球。"""
    _setup_logging(debug)
    logger.info("log file: {}", log_path())

    settings = GameSettings.load()
    settings.window.width = width
    settings.window.height = height
    settings.window.fps = fps
    settings.window.fullscreen = fullscreen

    engine = Engine(settings=settings, db_path=db)
    if profile:
        for p in engine.store.profiles.list_all():
            if p.name == profile:
                engine.profile = p
                engine.settings.active_profile_id = p.id
                break
    logger.info("Launching engine (profile={})",
                engine.profile.name if engine.profile else None)
    try:
        engine.run()
    except Exception:
        logger.exception("Engine crashed")
        raise


if __name__ == "__main__":
    app()
