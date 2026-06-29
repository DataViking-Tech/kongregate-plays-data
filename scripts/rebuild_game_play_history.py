#!/usr/bin/env python3
"""Rebuild combined game play history from archived and live metrics manifests."""

from __future__ import annotations

import csv
import json
import re
import urllib.parse
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_METRICS = ROOT / "data" / "raw" / "game_metrics"
ARCHIVE_MANIFEST_PATH = RAW_METRICS / "manifest.json"
LIVE_MANIFEST_PATH = RAW_METRICS / "live_manifest.json"
HISTORY_CSV = PROCESSED / "game_play_history.csv"
HISTORY_JSON = PROCESSED / "game_play_history.json"
WAYBACK_VIEW = "https://web.archive.org/web/{timestamp}/{original}"

HISTORY_COLUMNS = [
    "date",
    "game_name",
    "game_url",
    "plays_count_observed",
    "favorites_count_observed",
    "plays_text",
    "favorites_text",
    "metrics_url",
    "capture_timestamp",
    "capture_url",
    "parser",
    "confidence",
    "notes",
]


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def parse_int(value) -> int | str:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if value is None:
        return ""
    text = str(value)
    match = re.search(r"\d[\d,]*", text)
    if not match:
        return ""
    return int(match.group(0).replace(",", ""))


def canonical_game_url(game_url: str) -> str:
    if not game_url:
        return ""
    parsed = urllib.parse.urlsplit(game_url)
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/]+)", parsed.path)
    if not match:
        return game_url.lower()
    developer, slug = match.groups()
    return f"www.kongregate.com/games/{urllib.parse.unquote(developer)}/{urllib.parse.unquote(slug)}".lower()


def date_from_timestamp(timestamp: str) -> str:
    if len(timestamp) >= 8 and timestamp[:8].isdigit():
        return datetime.strptime(timestamp[:8], "%Y%m%d").date().isoformat()
    return ""


def row_from_metrics_payload(relative_path: str, meta: dict[str, str], parser: str) -> dict[str, object] | None:
    path = ROOT / relative_path
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(errors="replace"))
    except json.JSONDecodeError:
        return None

    plays = parse_int(payload.get("gameplays_count") or payload.get("gameplays_count_with_delimiter"))
    if not plays:
        return None
    favorites = parse_int(payload.get("favorites_count") or payload.get("favorites_count_with_delimiter"))
    timestamp = meta.get("capture_timestamp", "")
    original = meta.get("original_url", "")
    is_live = parser == "live_metrics_json"
    return {
        "date": date_from_timestamp(timestamp),
        "game_name": meta.get("game_name", ""),
        "game_url": meta.get("game_url", ""),
        "plays_count_observed": plays,
        "favorites_count_observed": favorites,
        "plays_text": payload.get("gameplays_count_with_delimiter", str(plays)),
        "favorites_text": payload.get("favorites_count_with_delimiter", str(favorites) if favorites else ""),
        "metrics_url": original,
        "capture_timestamp": timestamp,
        "capture_url": original if is_live else WAYBACK_VIEW.format(timestamp=timestamp, original=original),
        "parser": parser,
        "confidence": "high",
        "notes": (
            f"Fetched from live Kongregate metrics JSON {relative_path}"
            if is_live
            else f"Extracted from archived game metrics JSON {relative_path}"
        ),
    }


def rebuild_history() -> list[dict[str, object]]:
    rows = []
    seen = set()
    manifests = [
        (read_json(ARCHIVE_MANIFEST_PATH, {}), "metrics_json"),
        (read_json(LIVE_MANIFEST_PATH, {}), "live_metrics_json"),
    ]
    for manifest, parser in manifests:
        for relative_path, meta in sorted(manifest.items()):
            row = row_from_metrics_payload(relative_path, meta, parser)
            if not row:
                continue
            key = (
                canonical_game_url(str(row.get("game_url", ""))),
                row.get("capture_timestamp", ""),
                row.get("plays_count_observed", ""),
                row.get("parser", ""),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    rows.sort(key=lambda row: (row["date"], str(row["game_name"]).lower(), row["capture_timestamp"], row["parser"]))
    return rows


def write_history(rows: list[dict[str, object]]) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with HISTORY_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    HISTORY_JSON.write_text(json.dumps({"columns": HISTORY_COLUMNS, "rows": rows}, indent=2))


def main() -> None:
    rows = rebuild_history()
    write_history(rows)
    print(json.dumps({"history_rows": len(rows), "history_games": len({canonical_game_url(str(row.get("game_url", ""))) for row in rows})}, indent=2))


if __name__ == "__main__":
    main()
