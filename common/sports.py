"""Shared sport naming and gender-list constants."""

from __future__ import annotations

import re

from . import settings


MENS_ONLY_SPORTS = ["Football", "Baseball", "Rifle", "Crew"]
WOMENS_ONLY_SPORTS = ["Softball", "Beach Volleyball", "Field Hockey", "Bowling", "Equestrian", "Rugby"]

DEFAULT_SPORT_ALIASES = {
    "XC/TF": ["Track and Field", "TrackandField", "Track and Field, X-Country", "Cross Country", "XC"],
    "Swimming and Diving": ["Swimming and", "Swimming & Diving", "Swimming"],
    "Acrobatics and Tumbling": ["Acrobatics & Tumbling", "Acrobatics and Tumbling", "Acrobatics"],
    "Soccer": ["Soccer"],
}

BASE_SPORT_PATTERNS = {
    "acrobatics and tumbling": re.compile(r"acrobatics(\s*and.*)?", re.I),
    "baseball": re.compile(r"baseball", re.I),
    "basketball": re.compile(r"basketball", re.I),
    "beach volleyball": re.compile(r"beach\s*volleyball", re.I),
    "bowling": re.compile(r"bowling", re.I),
    "crew": re.compile(r"crew", re.I),
    "equestrian": re.compile(r"equestrian", re.I),
    "field hockey": re.compile(r"field\s*hockey", re.I),
    "golf": re.compile(r"golf", re.I),
    "gymnastics": re.compile(r"gymnastics", re.I),
    "triathlon": re.compile(r"triathlon", re.I),
    "football": re.compile(r"football", re.I),
    "lacrosse": re.compile(r"lacrosse", re.I),
    "rifle": re.compile(r"rifle", re.I),
    "skiing": re.compile(r"skiing", re.I),
    "soccer": re.compile(r"soccer", re.I),
    "softball": re.compile(r"softball", re.I),
    "stunt": re.compile(r"stunt", re.I),
    "fencing": re.compile(r"fencing", re.I),
    "ice hockey": re.compile(r"ice\s*hockey", re.I),
    "rowing": re.compile(r"rowing", re.I),
    "rugby": re.compile(r"rugby", re.I),
    "swimming and diving": re.compile(r"swimming(\s*and.*)?", re.I),
    "tennis": re.compile(r"tennis", re.I),
    "wrestling": re.compile(r"wrestling", re.I),
    "xc/tf": re.compile(r"(track|cross\s*country|xc)", re.I),
    "volleyball": re.compile(r"\bvolleyball\b", re.I),
    "water polo": re.compile(r"water\s*polo", re.I),
}


def get_sport_aliases() -> dict[str, list[str]]:
    return settings.get_sport_aliases(DEFAULT_SPORT_ALIASES)


def _build_sport_patterns() -> dict[str, re.Pattern]:
    patterns = dict(BASE_SPORT_PATTERNS)
    for canonical, aliases in get_sport_aliases().items():
        key = canonical.lower()
        escaped_aliases = [re.escape(alias) for alias in aliases if alias.strip()]
        if escaped_aliases:
            patterns[key] = re.compile("|".join(escaped_aliases), re.I)
    return patterns


SPORT_PATTERNS = _build_sport_patterns()


def _alias_matches(value: str, alias: str) -> bool:
    normalized_value = value.lower()
    normalized_alias = re.sub(r"\s+", " ", alias.strip().replace("&", "and")).lower()
    compact_value = re.sub(r"[^a-z0-9]", "", normalized_value)
    compact_alias = re.sub(r"[^a-z0-9]", "", normalized_alias)
    if not normalized_alias:
        return False
    return (
        normalized_alias == normalized_value
        or normalized_alias in normalized_value
        or compact_alias == compact_value
        or compact_alias in compact_value
    )


def normalize_sport_name(name: str) -> str:
    s = name.strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("&", "and")
    s = re.sub(r"\s*\(.*?\)\s*$", "", s)
    s = re.sub(r"[-'\".,;:]+$", "", s).strip()

    for canonical, aliases in get_sport_aliases().items():
        if any(_alias_matches(s, alias) for alias in aliases):
            return canonical

    return s.title()
