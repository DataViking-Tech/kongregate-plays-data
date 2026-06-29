#!/usr/bin/env python3
"""Fetch current Kongregate metrics.json snapshots for unresolved catalog games."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path

from rebuild_game_play_history import rebuild_history, write_history


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_METRICS = ROOT / "data" / "raw" / "game_metrics"
RAW_LIVE_JSON = RAW_METRICS / "live_json"
LOGS = ROOT / "logs"

CATALOG_CSV = PROCESSED / "mini_catalog.csv"
AUDIT_CSV = PROCESSED / "metrics_backfill_gap_audit.csv"
LIVE_MANIFEST_PATH = RAW_METRICS / "live_manifest.json"
FAILURE_PATH = RAW_METRICS / "live_failures.json"
REPORT_JSON = LOGS / "live_game_metrics_report.json"
REPORT_MD = LOGS / "live_game_metrics_report.md"
ERROR_LOG = LOGS / "live_game_metrics_errors.log"


@dataclass(frozen=True)
class CatalogGame:
    catalog_index: int
    game_url: str
    game_name: str
    status: str
    best_rank: int
    priority_score: int


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def timestamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def safe_name(text: str) -> str:
    text = urllib.parse.unquote(text)
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", text).strip("_")[:170]


def sha(text: str, length: int = 16) -> str:
    return sha1(text.encode("utf-8")).hexdigest()[:length]


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


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


def load_audit_statuses() -> dict[str, dict[str, str]]:
    rows = {}
    if not AUDIT_CSV.exists():
        return rows
    with AUDIT_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = canonical_game_url(row.get("game_url", ""))
            if key:
                rows[key] = row
    return rows


def load_catalog(statuses: set[str]) -> list[CatalogGame]:
    audit_rows = load_audit_statuses()
    games = []
    with CATALOG_CSV.open(newline="", encoding="utf-8") as handle:
        for catalog_index, row in enumerate(csv.DictReader(handle)):
            game_url = row.get("game_url", "")
            key = canonical_game_url(game_url)
            audit = audit_rows.get(key, {})
            status = audit.get("status", "unknown")
            if statuses and status not in statuses:
                continue
            games.append(
                CatalogGame(
                    catalog_index=catalog_index,
                    game_url=game_url,
                    game_name=row.get("game_name", ""),
                    status=status,
                    best_rank=int(row.get("best_rank") or 9999),
                    priority_score=int(audit.get("priority_score") or 0),
                )
            )
    return sorted(games, key=lambda game: (-game.priority_score, game.best_rank, game.catalog_index))


def load_input_csv(path: Path, statuses: set[str]) -> list[CatalogGame]:
    audit_rows = load_audit_statuses()
    games = []
    seen = set()
    with path.open(newline="", encoding="utf-8") as handle:
        for row_index, row in enumerate(csv.DictReader(handle)):
            game_url = row.get("game_url", "")
            key = canonical_game_url(game_url)
            if not key or key in seen:
                continue
            seen.add(key)
            audit = audit_rows.get(key, {})
            status = audit.get("status", "unknown")
            if statuses and status not in statuses:
                continue
            rank_text = row.get("rank") or row.get("best_rank") or audit.get("best_rank") or "9999"
            try:
                best_rank = int(rank_text)
            except ValueError:
                best_rank = 9999
            games.append(
                CatalogGame(
                    catalog_index=int(audit.get("catalog_index") or row_index),
                    game_url=game_url,
                    game_name=row.get("game_name", audit.get("game_name", "")),
                    status=status,
                    best_rank=best_rank,
                    priority_score=int(audit.get("priority_score") or max(0, 10000 - best_rank)),
                )
            )
    return games


def live_metrics_urls(game_url: str) -> list[str]:
    parsed = urllib.parse.urlsplit(game_url)
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/]+)", parsed.path)
    if not match:
        return []
    developer, slug = match.groups()
    paths = [
        f"/games/{developer}/{slug}/metrics.json",
        f"/en/games/{developer}/{slug}/metrics.json",
    ]
    urls = []
    for path in paths:
        urls.append(f"https://www.kongregate.com{path}")
    return list(dict.fromkeys(urls))


def live_cache_path(game: CatalogGame) -> Path:
    key = canonical_game_url(game.game_url)
    return RAW_LIVE_JSON / f"{safe_name(key)}_{sha(key)}.json"


def decode_payload(payload: bytes, headers) -> str:
    if payload[:2] == b"\x1f\x8b" or str(headers.get("Content-Encoding", "")).lower() == "gzip":
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass
    return payload.decode("utf-8", errors="replace")


def metrics_payload_is_valid(path: Path) -> bool:
    if not path.exists() or path.stat().st_size <= 0:
        return False
    try:
        payload = json.loads(path.read_text(errors="replace"))
    except json.JSONDecodeError:
        return False
    return bool(parse_int(payload.get("gameplays_count") or payload.get("gameplays_count_with_delimiter")))


def fetch_live_metrics(game: CatalogGame, timeout_s: int) -> tuple[bool, str, str]:
    target = live_cache_path(game)
    if metrics_payload_is_valid(target):
        return True, "cached", ""

    last_error = ""
    for url in live_metrics_urls(game.game_url):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "KongregateLiveMetricsBackfill/0.1", "Accept": "application/json,text/plain,*/*"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                payload_text = decode_payload(response.read(), response.headers)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                last_error = "http_404"
                continue
            try:
                payload_text = decode_payload(exc.read(), exc.headers)
            except Exception:
                last_error = f"http_{exc.code}"
                continue
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            last_error = str(exc)
            continue

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            last_error = "not_json"
            continue
        if not parse_int(payload.get("gameplays_count") or payload.get("gameplays_count_with_delimiter")):
            last_error = "no_gameplays_count"
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True))
        return True, str(target.relative_to(ROOT)), url

    return False, last_error or "request_failed", ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch current live metrics.json snapshots for unresolved Kongregate catalog games.")
    parser.add_argument("--statuses", default="no_cdx,known_failures_only", help="Comma-separated metrics audit statuses to target.")
    parser.add_argument("--input-csv", default="", help="Optional CSV of explicit games to target; must include game_url and game_name columns. Use --statuses '' to ignore audit status.")
    parser.add_argument("--catalog-offset", type=int, default=0, help="Skip this many targeted catalog rows.")
    parser.add_argument("--catalog-limit", type=int, default=0, help="Limit targeted catalog rows. 0 means all remaining.")
    parser.add_argument("--max-fetches", type=int, default=0, help="Limit live metric attempts. 0 means all targeted pending.")
    parser.add_argument("--timeout", type=int, default=18, help="Per-request timeout in seconds.")
    parser.add_argument("--sleep", type=float, default=0.25, help="Seconds to sleep after each live metrics attempt.")
    parser.add_argument("--refresh", action="store_true", help="Refetch even if a valid live metrics cache exists.")
    args = parser.parse_args()

    for directory in (RAW_LIVE_JSON, PROCESSED, LOGS):
        directory.mkdir(parents=True, exist_ok=True)

    statuses = {status.strip() for status in args.statuses.split(",") if status.strip()}
    catalog = load_input_csv(ROOT / args.input_csv, statuses) if args.input_csv else load_catalog(statuses)
    scope = catalog[args.catalog_offset :]
    if args.catalog_limit:
        scope = scope[: args.catalog_limit]

    manifest = read_json(LIVE_MANIFEST_PATH, {})
    failures = read_json(FAILURE_PATH, {})
    timestamp = timestamp_now()
    pending = []
    for game in scope:
        relative = str(live_cache_path(game).relative_to(ROOT))
        if args.refresh or not metrics_payload_is_valid(live_cache_path(game)) or relative not in manifest:
            pending.append(game)

    selected = pending if args.max_fetches == 0 else pending[: args.max_fetches]
    fetched = 0
    cached = 0
    failed = 0
    for game in selected:
        ok, detail, url = fetch_live_metrics(game, args.timeout)
        relative = str(live_cache_path(game).relative_to(ROOT))
        key = canonical_game_url(game.game_url)
        if ok:
            if detail == "cached":
                cached += 1
                url = manifest.get(relative, {}).get("original_url", live_metrics_urls(game.game_url)[0])
            else:
                fetched += 1
            manifest[relative] = {
                "game_url": game.game_url,
                "game_name": game.game_name,
                "capture_timestamp": timestamp,
                "original_url": url,
                "source_status": game.status,
            }
            failures.pop(key, None)
        else:
            failed += 1
            failures[key] = {
                "game_url": game.game_url,
                "game_name": game.game_name,
                "status": game.status,
                "last_error": detail,
                "last_attempt_timestamp": utc_now(),
            }
            ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\tlive_json\t{game.game_url}\t{detail}\n")
        time.sleep(args.sleep)

    write_json(LIVE_MANIFEST_PATH, manifest)
    write_json(FAILURE_PATH, failures)
    history_rows = rebuild_history()
    write_history(history_rows)

    report = {
        "run_timestamp": utc_now(),
        "statuses": sorted(statuses),
        "targeted_games": len(catalog),
        "catalog_offset": args.catalog_offset,
        "catalog_limit": args.catalog_limit,
        "games_in_scope": len(scope),
        "pending_before_run": len(pending),
        "attempted_this_run": len(selected),
        "fetched_this_run": fetched,
        "cached_selected_this_run": cached,
        "failed_this_run": failed,
        "live_manifest_entries": len(manifest),
        "known_live_failures": len(failures),
        "history_rows": len(history_rows),
        "history_games": len({canonical_game_url(str(row.get("game_url", ""))) for row in history_rows}),
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Kongregate Live Game Metrics Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- Target statuses: {', '.join(report['statuses'])}",
                f"- Targeted games: {report['targeted_games']}",
                f"- Games in scope: {report['games_in_scope']}",
                f"- Pending before run: {report['pending_before_run']}",
                f"- Attempted this run: {report['attempted_this_run']}",
                f"- Fetched this run: {report['fetched_this_run']}",
                f"- Failed this run: {report['failed_this_run']}",
                f"- Live manifest entries: {report['live_manifest_entries']}",
                f"- Known live failures: {report['known_live_failures']}",
                f"- Combined history rows: {report['history_rows']}",
                f"- Combined history games: {report['history_games']}",
                "",
            ]
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
