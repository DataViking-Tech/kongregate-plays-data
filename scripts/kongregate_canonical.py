#!/usr/bin/env python3
"""Canonical Kongregate game identity helpers."""

from __future__ import annotations

import re
import urllib.parse


# Explicit developer/owner rename aliases. Do not collapse by title alone:
# Kongregate has many unrelated games with generic names like "Pong" and
# "Snake", so aliases stay opt-in and evidence-backed.
CANONICAL_GAME_ALIASES = {
    "www.kongregate.com/games/dragongamez/bowmaster-prelude": "www.kongregate.com/games/lostvector/bowmaster-prelude",
    "www.kongregate.com/games/igorlevochkin/counter-strike-web-browser-based-port-v2": "www.kongregate.com/games/criticalforceet/counter-strike-web-browser-based-port-v2",
    "www.kongregate.com/games/colinnorthway/fantastic-contraption": "www.kongregate.com/games/inxile_ent/fantastic-contraption",
    "www.kongregate.com/games/thegamehomepage/super-stacker-2": "www.kongregate.com/games/inxile_ent/super-stacker-2",
    "www.kongregate.com/games/freefall_wel/freefall-tournament": "www.kongregate.com/games/freerangegames/freefall-tournament",
    "www.kongregate.com/games/spiralknights/spiral-knights": "www.kongregate.com/games/greyhavens/spiral-knights",
    "www.kongregate.com/games/tigrounette/transformice": "www.kongregate.com/games/atelier801/transformice",
    "www.kongregate.com/games/gamerdisclaimer/murloc-rpg-stranglethorn-fever": "www.kongregate.com/games/unmediocre/murloc-rpg-stranglethorn-fever",
}


def normalized_game_url(game_url: str) -> str:
    if not game_url:
        return ""
    parsed = urllib.parse.urlsplit(game_url)
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/]+)", parsed.path)
    if not match:
        return game_url.lower()
    developer, slug = match.groups()
    return f"www.kongregate.com/games/{urllib.parse.unquote(developer)}/{urllib.parse.unquote(slug)}".lower()


def canonical_game_url(game_url: str) -> str:
    normalized = normalized_game_url(game_url)
    return CANONICAL_GAME_ALIASES.get(normalized, normalized)
