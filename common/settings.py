"""Persistent local user settings for the desktop app."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


APP_NAME = "NCAA Report Tool"
SETTINGS_VERSION = 2


DEFAULT_SETTINGS = {
    "version": SETTINGS_VERSION,
    "last_pdf_folder": "",
    "last_save_directory": "",
    "last_include_client": True,
    "recent_pdf_folders": [],
    "verbose_logging": False,
    "preferred_output_filename_pattern": "{workflow}_{client}_{date}.xlsx",
    "custom_sport_aliases": {},
    "sport_aliases": None,
    "sportops_tables": None,
    "sportops_output_tables": None,
    "log_directory": "",
}


class SettingsStore:
    """Small JSON-backed settings store with validation and fallback defaults."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings_path()

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return DEFAULT_SETTINGS.copy()

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return DEFAULT_SETTINGS.copy()

        return _validate_settings(data)

    def save(self, settings: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = _validate_settings(settings)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")


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


def logs_dir() -> Path:
    configured = load_settings().get("log_directory", "")
    if configured:
        return Path(configured)
    return default_logs_dir()


def default_logs_dir() -> Path:
    return _settings_dir() / "logs"


def reset_log_directory() -> None:
    next_settings = load_settings()
    next_settings["log_directory"] = ""
    save_settings(next_settings)


def _clean_alias_mapping(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}

    clean_aliases = {}
    for canonical, values in value.items():
        canonical_name = str(canonical).strip()
        if not canonical_name:
            continue
        if isinstance(values, str):
            values = [values]
        if isinstance(values, list):
            clean_values = []
            seen = set()
            for item in values:
                alias = str(item).strip()
                if not alias:
                    continue
                key = alias.casefold()
                if key in seen:
                    continue
                seen.add(key)
                clean_values.append(alias)
            if clean_values:
                clean_aliases[canonical_name] = clean_values
    return clean_aliases


def _merge_alias_mappings(*mappings: dict[str, list[str]]) -> dict[str, list[str]]:
    merged = {}
    canonical_lookup = {}
    for mapping in mappings:
        for canonical, aliases in mapping.items():
            key = canonical.casefold()
            target = canonical_lookup.setdefault(key, canonical)
            merged.setdefault(target, [])
            seen = {alias.casefold() for alias in merged[target]}
            for alias in aliases:
                if alias.casefold() in seen:
                    continue
                seen.add(alias.casefold())
                merged[target].append(alias)
    return merged


def _clean_string_list(value: Any) -> list[str] | None:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return None

    cleaned = []
    seen = set()
    for item in value:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned


def _clean_string_mapping(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None

    cleaned = {}
    for key, label in value.items():
        key = str(key).strip()
        label = str(label).strip()
        if not key or not label or key in cleaned:
            continue
        cleaned[key] = label
    return cleaned


def _validate_settings(data: Any) -> dict[str, Any]:
    settings = DEFAULT_SETTINGS.copy()
    if isinstance(data, dict):
        settings.update(data)

    settings["version"] = SETTINGS_VERSION
    settings["last_pdf_folder"] = str(settings.get("last_pdf_folder") or "")
    settings["last_save_directory"] = str(settings.get("last_save_directory") or "")
    settings["last_include_client"] = bool(settings.get("last_include_client", True))
    settings["verbose_logging"] = bool(settings.get("verbose_logging", False))
    settings["preferred_output_filename_pattern"] = str(
        settings.get("preferred_output_filename_pattern")
        or DEFAULT_SETTINGS["preferred_output_filename_pattern"]
    )
    settings["log_directory"] = str(settings.get("log_directory") or "")

    recent = settings.get("recent_pdf_folders", [])
    if not isinstance(recent, list):
        recent = []
    settings["recent_pdf_folders"] = [str(path) for path in recent if path][:5]

    settings["custom_sport_aliases"] = _clean_alias_mapping(settings.get("custom_sport_aliases", {}))
    sport_aliases = settings.get("sport_aliases")
    settings["sport_aliases"] = _clean_alias_mapping(sport_aliases) if isinstance(sport_aliases, dict) else None
    settings["sportops_tables"] = _clean_string_mapping(settings.get("sportops_tables"))
    settings["sportops_output_tables"] = _clean_string_list(settings.get("sportops_output_tables"))
    return settings


def load_settings() -> dict[str, Any]:
    return SettingsStore().load()


def save_settings(settings: dict[str, Any]) -> None:
    SettingsStore().save(settings)


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


def update_setting(key: str, value: Any) -> None:
    settings = load_settings()
    settings[key] = value
    save_settings(settings)


def get_custom_sport_aliases() -> dict[str, list[str]]:
    return load_settings().get("custom_sport_aliases", {})


def get_sport_aliases(default_aliases: dict[str, list[str]]) -> dict[str, list[str]]:
    current_settings = load_settings()
    saved_aliases = current_settings.get("sport_aliases")
    if saved_aliases is not None:
        return saved_aliases
    return _merge_alias_mappings(default_aliases, current_settings.get("custom_sport_aliases", {}))


def save_sport_aliases(alias_mapping: dict[str, list[str]]) -> None:
    next_settings = load_settings()
    next_settings["sport_aliases"] = _clean_alias_mapping(alias_mapping)
    save_settings(next_settings)


def clean_sportops_output_tables(value: Any, default_table_ids: list[str]) -> list[str]:
    default_ids = [str(table_id) for table_id in default_table_ids]
    raw_ids = _clean_string_list(value)
    if raw_ids is None:
        return default_ids

    allowed = set(default_ids)
    selected = [table_id for table_id in raw_ids if table_id in allowed]
    return selected or default_ids


def clean_sportops_tables(value: Any, default_tables: dict[str, str]) -> dict[str, str]:
    cleaned = _clean_string_mapping(value)
    return cleaned or {str(key): str(label) for key, label in default_tables.items()}


def get_sportops_tables(default_tables: dict[str, str]) -> dict[str, str]:
    return clean_sportops_tables(load_settings().get("sportops_tables"), default_tables)


def save_sportops_tables(table_map: dict[str, str], default_tables: dict[str, str]) -> None:
    next_settings = load_settings()
    next_settings["sportops_tables"] = clean_sportops_tables(table_map, default_tables)
    next_settings["sportops_output_tables"] = list(next_settings["sportops_tables"])
    save_settings(next_settings)


def get_sportops_output_tables(default_table_ids: list[str]) -> list[str]:
    return clean_sportops_output_tables(
        load_settings().get("sportops_output_tables"),
        default_table_ids,
    )


def save_sportops_output_tables(table_ids: list[str], default_table_ids: list[str]) -> None:
    next_settings = load_settings()
    next_settings["sportops_output_tables"] = clean_sportops_output_tables(table_ids, default_table_ids)
    save_settings(next_settings)


def reset_sportops_output_tables(default_table_ids: list[str]) -> None:
    next_settings = load_settings()
    next_settings["sportops_output_tables"] = [str(table_id) for table_id in default_table_ids]
    save_settings(next_settings)


def reset_sportops_tables(default_tables: dict[str, str]) -> None:
    next_settings = load_settings()
    next_settings["sportops_tables"] = {str(key): str(label) for key, label in default_tables.items()}
    next_settings["sportops_output_tables"] = list(next_settings["sportops_tables"])
    save_settings(next_settings)
