#!/usr/bin/env python3
"""Rebuild combined game play history from archived and live metrics manifests."""

from __future__ import annotations

import csv
import json
import re
import urllib.parse
from datetime import datetime
from pathlib import Path

from kongregate_canonical import canonical_game_url as shared_canonical_game_url


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_METRICS = ROOT / "data" / "raw" / "game_metrics"
ARCHIVE_MANIFEST_PATH = RAW_METRICS / "manifest.json"
LIVE_MANIFEST_PATH = RAW_METRICS / "live_manifest.json"
GAME_PAGE_MANIFEST_PATH = ROOT / "data" / "raw" / "game_pages" / "manifest.json"
COUNT_SOURCE_PLAY_COUNTS_PATH = PROCESSED / "count_source_play_counts.csv"
COUNT_SOURCE_CANDIDATES_PATH = PROCESSED / "count_source_probe_candidates.csv"
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
    return shared_canonical_game_url(game_url)


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


def row_from_game_page_meta(relative_path: str, meta: dict[str, str]) -> dict[str, object] | None:
    path = ROOT / relative_path
    if not path.exists():
        return None
    plays = parse_int(meta.get("plays_count_observed") or meta.get("plays_text"))
    if not plays:
        return None
    favorites = parse_int(meta.get("favorites_count_observed") or meta.get("favorites_text"))
    timestamp = meta.get("capture_timestamp", "")
    original = meta.get("original_url", "")
    return {
        "date": date_from_timestamp(timestamp),
        "game_name": meta.get("game_name", ""),
        "game_url": meta.get("game_url", ""),
        "plays_count_observed": plays,
        "favorites_count_observed": favorites,
        "plays_text": meta.get("plays_text", str(plays)),
        "favorites_text": meta.get("favorites_text", str(favorites) if favorites else ""),
        "metrics_url": original,
        "capture_timestamp": timestamp,
        "capture_url": WAYBACK_VIEW.format(timestamp=timestamp, original=original),
        "parser": "game_page_html",
        "confidence": meta.get("confidence", "high"),
        "notes": meta.get("notes", f"Extracted from archived game page HTML {relative_path}"),
    }


def row_from_count_source_candidate(candidate: dict[str, str]) -> dict[str, object] | None:
    plays = parse_int(candidate.get("parsed_plays"))
    timestamp = candidate.get("sample_timestamp", "")
    original = candidate.get("sample_original", "")
    if not plays or not timestamp or not original:
        return None

    payload = {}
    relative_path = candidate.get("sample_path", "")
    path = ROOT / relative_path if relative_path else None
    if path and path.exists():
        try:
            payload = json.loads(path.read_text(errors="replace"))
        except json.JSONDecodeError:
            payload = {}

    favorites = parse_int(payload.get("favorites_count") or payload.get("favorites_count_with_delimiter"))
    target_key = canonical_game_url(candidate.get("game_url", ""))
    sample_key = canonical_game_url(original)
    confidence = "high" if sample_key == target_key else "medium"
    alias_note = "" if sample_key == target_key else f"; sample canonical URL {sample_key} differs from target {target_key}"
    return {
        "date": date_from_timestamp(timestamp),
        "game_name": candidate.get("game_name", ""),
        "game_url": candidate.get("game_url", ""),
        "plays_count_observed": plays,
        "favorites_count_observed": favorites,
        "plays_text": payload.get("gameplays_count_with_delimiter", str(plays)),
        "favorites_text": payload.get("favorites_count_with_delimiter", str(favorites) if favorites else ""),
        "metrics_url": original,
        "capture_timestamp": timestamp,
        "capture_url": WAYBACK_VIEW.format(timestamp=timestamp, original=original),
        "parser": "count_source_probe",
        "confidence": confidence,
        "notes": (
            "Recovered from archived count-source probe "
            f"{relative_path}; source={candidate.get('source_type', '')}; "
            f"signal={candidate.get('count_signal', '')}{alias_note}"
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
    for relative_path, meta in sorted(read_json(GAME_PAGE_MANIFEST_PATH, {}).items()):
        row = row_from_game_page_meta(relative_path, meta)
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
    for count_source_path in (COUNT_SOURCE_PLAY_COUNTS_PATH, COUNT_SOURCE_CANDIDATES_PATH):
        if not count_source_path.exists():
            continue
        for candidate in csv.DictReader(count_source_path.open(newline="", encoding="utf-8")):
            row = row_from_count_source_candidate(candidate)
            if not row:
                continue
            key = (
                canonical_game_url(str(row.get("game_url", ""))),
                row.get("capture_timestamp", ""),
                row.get("plays_count_observed", ""),
                row.get("parser", ""),
                row.get("metrics_url", ""),
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
        writer = csv.DictWriter(handle, fieldnames=HISTORY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    HISTORY_JSON.write_text(json.dumps({"columns": HISTORY_COLUMNS, "rows": rows}, indent=2))


def main() -> None:
    rows = rebuild_history()
    write_history(rows)
    print(json.dumps({"history_rows": len(rows), "history_games": len({canonical_game_url(str(row.get("game_url", ""))) for row in rows})}, indent=2))


if __name__ == "__main__":
    main()
