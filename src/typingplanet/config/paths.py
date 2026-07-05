"""Cross-platform filesystem paths for user data and settings.

Honours ``TYPINGPLANET_DATA_DIR`` / ``TYPINGPLANET_CONFIG_DIR`` overrides (useful
for tests and portable installs). If the preferred location is not writable the
app falls back to a ``.typingplanet`` folder in the working directory so it
never fails to launch over a permission issue.
"""
from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "TypingPlanet"
APP_AUTHOR = "TypingPlanet"


def _resolve(preferred: Path, fallback_name: str) -> Path:
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred
    except (PermissionError, OSError):
        fb = Path.cwd() / ".typingplanet" / fallback_name
        fb.mkdir(parents=True, exist_ok=True)
        return fb


def data_dir() -> Path:
    override = os.environ.get("TYPINGPLANET_DATA_DIR")
    preferred = Path(override) if override else Path(user_data_dir(APP_NAME, APP_AUTHOR))
    return _resolve(preferred, "data")


def config_dir() -> Path:
    override = os.environ.get("TYPINGPLANET_CONFIG_DIR")
    preferred = Path(override) if override else Path(user_config_dir(APP_NAME, APP_AUTHOR))
    return _resolve(preferred, "config")


def db_path() -> Path:
    return data_dir() / "typingplanet.db"


def settings_path() -> Path:
    return config_dir() / "settings.json"


def log_path() -> Path:
    return data_dir() / "typingplanet.log"
