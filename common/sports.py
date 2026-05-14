"""Shared sport naming and gender-list constants."""

from __future__ import annotations

import re


MENS_ONLY_SPORTS = ["Football", "Baseball", "Rifle", "Crew"]
WOMENS_ONLY_SPORTS = ["Softball", "Beach Volleyball", "Field Hockey", "Bowling", "Equestrian", "Rugby"]

SPORT_PATTERNS = {
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


def normalize_sport_name(name: str) -> str:
    s = name.strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("&", "and")
    s = re.sub(r"\s*\(.*?\)\s*$", "", s)
    s = re.sub(r"[-'\".,;:]+$", "", s).strip()

    if re.search(r"track\s*(?:and|&)\s*field\s*,?\s*x", s, flags=re.I):
        return "XC/TF"
    if re.search(r"\bsoccer\b", s, flags=re.I):
        return "Soccer"
    if re.search(r"swimming\s*and", s, flags=re.I):
        return "Swimming and Diving"
    if re.search(r"acrobatics\s*(?:and|&)(?:\s*tumbling)?", s, flags=re.I) or "acrobatics" in s.lower():
        return "Acrobatics and Tumbling"

    return s.title()
