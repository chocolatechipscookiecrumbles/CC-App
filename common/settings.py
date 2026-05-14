"""Persistent local user settings for the desktop app."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


APP_NAME = "NCAA Report Tool"
SETTINGS_VERSION = 1


DEFAULT_SETTINGS = {
    "version": SETTINGS_VERSION,
    "last_pdf_folder": "",
    "last_save_directory": "",
    "last_include_client": True,
    "recent_pdf_folders": [],
}


def _settings_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_NAME
    return Path.home() / ".config" / "ncaa-report-tool"


def settings_path() -> Path:
    return _settings_dir() / "settings.json"


def load_settings() -> dict[str, Any]:
    path = settings_path()
    if not path.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_SETTINGS.copy()

    settings = DEFAULT_SETTINGS.copy()
    if isinstance(data, dict):
        settings.update(data)
    settings["version"] = SETTINGS_VERSION
    return settings


def save_settings(settings: dict[str, Any]) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = DEFAULT_SETTINGS.copy()
    data.update(settings)
    data["version"] = SETTINGS_VERSION
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_initial_directory(key: str) -> str | None:
    value = load_settings().get(key, "")
    if value and os.path.isdir(value):
        return value
    return None


def remember_pdf_folder(folder_path: str) -> None:
    settings = load_settings()
    settings["last_pdf_folder"] = folder_path

    recent = [path for path in settings.get("recent_pdf_folders", []) if path != folder_path]
    recent.insert(0, folder_path)
    settings["recent_pdf_folders"] = recent[:5]
    save_settings(settings)


def remember_save_path(output_path: str) -> None:
    settings = load_settings()
    directory = os.path.dirname(output_path)
    if directory:
        settings["last_save_directory"] = directory
    save_settings(settings)


def remember_include_client(include_client: bool) -> None:
    settings = load_settings()
    settings["last_include_client"] = bool(include_client)
    save_settings(settings)
