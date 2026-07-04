#!/usr/bin/env python3
"""Check current Kongregate game-page availability for lifecycle evidence."""

from __future__ import annotations

import argparse
import csv
import gzip
import html
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

from kongregate_canonical import canonical_game_url, normalized_game_url


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_GAME_PAGES = ROOT / "data" / "raw" / "game_pages"
RAW_LIVE_HTML = RAW_GAME_PAGES / "live_html"
LOGS = ROOT / "logs"

MINI_CATALOG_CSV = PROCESSED / "mini_catalog.csv"
LIFECYCLE_CSV = PROCESSED / "game_lifecycle_catalog.csv"
STATUS_JSON = RAW_GAME_PAGES / "live_page_status.json"
STATUS_CSV = PROCESSED / "live_game_page_status.csv"
STATUS_EXPORT_JSON = PROCESSED / "live_game_page_status.json"
REPORT_JSON = LOGS / "live_game_page_report.json"
REPORT_MD = LOGS / "live_game_page_report.md"
ERROR_LOG = LOGS / "live_game_page_errors.log"

GAME_URL_RE = re.compile(r"^/(?:en/)?games/([^/]+)/([^/]+)")
CANONICAL_RE = re.compile(
    r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']+)[\"']|"
    r"<link[^>]+href=[\"']([^\"']+)[\"'][^>]+rel=[\"']canonical[\"']",
    re.IGNORECASE,
)
OG_URL_RE = re.compile(r"<meta[^>]+property=[\"']og:url[\"'][^>]+content=[\"']([^\"']+)[\"']", re.IGNORECASE)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
UNAVAILABLE_RE = re.compile(
    r"(the page you were looking for doesn'?t exist|"
    r"game not found|"
    r"this game is no longer available|"
    r"this game has been removed|"
    r"404)",
    re.IGNORECASE,
)

STATUS_COLUMNS = [
    "canonical_game_key",
    "game_name",
    "game_url",
    "best_rank",
    "status",
    "http_status",
    "final_url",
    "matched_url",
    "page_canonical_key",
    "canonical_match",
    "title",
    "last_attempt_timestamp",
    "previous_removal_evidence_status",
    "current_live_metric_status",
    "unavailable_reason",
    "cache_path",
]


@dataclass(frozen=True)
class CatalogGame:
    catalog_index: int
    game_name: str
    game_url: str
    game_url_variants: tuple[str, ...]
    best_rank: int
    removal_evidence_status: str
    current_live_metric_status: str


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def timestamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def sha(text: str, length: int = 16) -> str:
    return sha1(text.encode("utf-8")).hexdigest()[:length]


def safe_name(text: str) -> str:
    text = urllib.parse.unquote(text)
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", text).strip("_")[:170]


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def write_status_exports(statuses: dict[str, dict[str, str]]) -> None:
    rows = []
    for key, row in statuses.items():
        exported = {column: row.get(column, "") for column in STATUS_COLUMNS}
        exported["canonical_game_key"] = exported["canonical_game_key"] or key
        rows.append(exported)
    rows.sort(key=lambda row: (parse_int(row.get("best_rank"), 9999), row.get("game_name", "").lower()))

    PROCESSED.mkdir(parents=True, exist_ok=True)
    with STATUS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=STATUS_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    STATUS_EXPORT_JSON.write_text(json.dumps({"columns": STATUS_COLUMNS, "rows": rows}, indent=2))


def split_semicolon(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in (value or "").split(";") if part.strip())


def parse_int(value: str, default: int = 9999) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_games(args: argparse.Namespace) -> list[CatalogGame]:
    source_path = ROOT / args.input_csv if args.input_csv else LIFECYCLE_CSV
    if not source_path.exists():
        source_path = MINI_CATALOG_CSV

    removal_statuses = {part.strip() for part in args.removal_statuses.split(",") if part.strip()}
    metric_statuses = {part.strip() for part in args.metric_statuses.split(",") if part.strip()}

    games = []
    seen = set()
    with source_path.open(newline="", encoding="utf-8") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            game_url = row.get("game_url", "")
            key = canonical_game_url(game_url)
            if not key or key in seen:
                continue
            removal_status = row.get("removal_evidence_status", "")
            metric_status = row.get("current_live_metric_status", "")
            if removal_statuses and removal_status not in removal_statuses:
                continue
            if metric_statuses and metric_status not in metric_statuses:
                continue
            seen.add(key)
            variants = [game_url]
            variants.extend(split_semicolon(row.get("game_url_variants", "")))
            games.append(
                CatalogGame(
                    catalog_index=index,
                    game_name=row.get("game_name", ""),
                    game_url=game_url,
                    game_url_variants=tuple(dict.fromkeys(part for part in variants if part)),
                    best_rank=parse_int(row.get("best_rank")),
                    removal_evidence_status=removal_status,
                    current_live_metric_status=metric_status,
                )
            )
    return sorted(games, key=lambda game: (game.best_rank, game.catalog_index))


def live_urls_for_game_url(game_url: str) -> list[str]:
    parsed = urllib.parse.urlsplit(game_url)
    match = GAME_URL_RE.match(parsed.path)
    if not match:
        return []
    developer, slug = (urllib.parse.quote(urllib.parse.unquote(part), safe="") for part in match.groups())
    paths = [
        f"/games/{developer}/{slug}",
        f"/en/games/{developer}/{slug}",
    ]
    urls = [f"https://www.kongregate.com{path}" for path in paths]
    normalized = normalized_game_url(game_url)
    if normalized:
        urls.append(f"https://{normalized}")
    return list(dict.fromkeys(urls))


def live_urls(game: CatalogGame) -> list[str]:
    urls = []
    for variant in game.game_url_variants:
        urls.extend(live_urls_for_game_url(variant))
    return list(dict.fromkeys(urls))


def decode_payload(payload: bytes, headers) -> str:
    if payload[:2] == b"\x1f\x8b" or str(headers.get("Content-Encoding", "")).lower() == "gzip":
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass
    return payload.decode("utf-8", errors="replace")


def extract_page_canonical_key(markup: str, fallback_url: str) -> str:
    for pattern in (CANONICAL_RE, OG_URL_RE):
        for match in pattern.finditer(markup):
            url = next((group for group in match.groups() if group), "")
            key = canonical_game_url(html.unescape(url))
            if key:
                return key
    return canonical_game_url(fallback_url)


def extract_title(markup: str) -> str:
    match = TITLE_RE.search(markup)
    if not match:
        return ""
    return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()[:180]


def live_cache_path(game: CatalogGame, timestamp: str) -> Path:
    key = canonical_game_url(game.game_url)
    return RAW_LIVE_HTML / f"{timestamp}_{safe_name(key)}_{sha(key)}.html"


def cached_status_is_fresh(row: dict[str, str], max_age_days: int) -> bool:
    if max_age_days <= 0:
        return False
    attempt = row.get("last_attempt_timestamp", "")
    if not attempt:
        return False
    try:
        attempt_date = datetime.strptime(attempt[:10], "%Y-%m-%d").date()
    except ValueError:
        return False
    age = (datetime.now(timezone.utc).date() - attempt_date).days
    return age <= max_age_days


def classify_success(game: CatalogGame, url: str, final_url: str, status_code: int, markup: str, timestamp: str) -> dict[str, str]:
    expected_key = canonical_game_url(game.game_url)
    page_key = extract_page_canonical_key(markup, final_url or url)
    title = extract_title(markup)
    unavailable_match = UNAVAILABLE_RE.search(markup)
    if unavailable_match and (not page_key or page_key != expected_key):
        return {
            "status": "live_page_unavailable_text",
            "http_status": str(status_code),
            "final_url": final_url or url,
            "matched_url": url,
            "page_canonical_key": page_key,
            "canonical_match": "no",
            "title": title,
            "cache_path": "",
            "unavailable_reason": unavailable_match.group(1)[:80],
        }

    target = live_cache_path(game, timestamp)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markup)
    return {
        "status": "live_page_available",
        "http_status": str(status_code),
        "final_url": final_url or url,
        "matched_url": url,
        "page_canonical_key": page_key,
        "canonical_match": "yes" if page_key == expected_key else "unknown",
        "title": title,
        "cache_path": str(target.relative_to(ROOT)),
        "unavailable_reason": "",
    }


def fetch_live_page(game: CatalogGame, timeout_s: int, timestamp: str) -> dict[str, str]:
    last_error = ""
    for url in live_urls(game):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "KongregateLifecyclePageCheck/0.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                markup = decode_payload(response.read(), response.headers)
                return classify_success(game, url, response.geturl(), response.status, markup, timestamp)
        except urllib.error.HTTPError as exc:
            if exc.code in {404, 410}:
                return {
                    "status": f"live_page_http_{exc.code}",
                    "http_status": str(exc.code),
                    "final_url": exc.geturl() or url,
                    "matched_url": url,
                    "page_canonical_key": "",
                    "canonical_match": "no",
                    "title": "",
                    "cache_path": "",
                    "unavailable_reason": f"http_{exc.code}",
                }
            last_error = f"http_{exc.code}"
            continue
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            last_error = str(exc.reason if hasattr(exc, "reason") else exc)
            continue

    return {
        "status": "live_page_request_failed",
        "http_status": "",
        "final_url": "",
        "matched_url": "",
        "page_canonical_key": "",
        "canonical_match": "unknown",
        "title": "",
        "cache_path": "",
        "unavailable_reason": last_error or "request_failed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check current public Kongregate game-page availability.")
    parser.add_argument("--input-csv", default="", help="Optional CSV with game_url/game_name rows. Defaults to lifecycle catalog.")
    parser.add_argument("--removal-statuses", default="live_metrics_unavailable", help="Comma-separated lifecycle removal statuses to target. Use '' for all.")
    parser.add_argument("--metric-statuses", default="", help="Comma-separated live metric statuses to target. Use '' for all.")
    parser.add_argument("--catalog-offset", type=int, default=0, help="Skip this many targeted rows.")
    parser.add_argument("--catalog-limit", type=int, default=0, help="Limit targeted rows before pending filtering. 0 means all.")
    parser.add_argument("--max-fetches", type=int, default=0, help="Limit live page requests. 0 means all pending.")
    parser.add_argument("--timeout", type=int, default=18, help="Per-request timeout in seconds.")
    parser.add_argument("--sleep", type=float, default=0.25, help="Seconds to sleep after each game check.")
    parser.add_argument("--refresh", action="store_true", help="Refetch even if a fresh live page status exists.")
    parser.add_argument("--fresh-days", type=int, default=7, help="Skip cached statuses newer than this many days unless refreshing.")
    args = parser.parse_args()

    RAW_LIVE_HTML.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    catalog = load_games(args)
    scope = catalog[args.catalog_offset :]
    if args.catalog_limit:
        scope = scope[: args.catalog_limit]

    statuses = read_json(STATUS_JSON, {})
    pending = []
    fresh_skipped = 0
    for game in scope:
        key = canonical_game_url(game.game_url)
        if not args.refresh and cached_status_is_fresh(statuses.get(key, {}), args.fresh_days):
            fresh_skipped += 1
            continue
        pending.append(game)

    selected = pending if args.max_fetches == 0 else pending[: args.max_fetches]
    timestamp = timestamp_now()
    counts = {"available": 0, "unavailable": 0, "failed": 0}
    for game in selected:
        key = canonical_game_url(game.game_url)
        result = fetch_live_page(game, args.timeout, timestamp)
        status = result["status"]
        if status == "live_page_available":
            counts["available"] += 1
        elif status.startswith("live_page_http_") or status == "live_page_unavailable_text":
            counts["unavailable"] += 1
        else:
            counts["failed"] += 1
            ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\tlive_page\t{game.game_url}\t{result.get('unavailable_reason', '')}\n")
        statuses[key] = {
            "canonical_game_key": key,
            "game_url": game.game_url,
            "game_name": game.game_name,
            "best_rank": game.best_rank,
            "previous_removal_evidence_status": game.removal_evidence_status,
            "current_live_metric_status": game.current_live_metric_status,
            "last_attempt_timestamp": utc_now(),
            **result,
        }
        time.sleep(args.sleep)

    write_json(STATUS_JSON, statuses)
    write_status_exports(statuses)
    status_counts = {}
    for row in statuses.values():
        status_counts[row.get("status", "")] = status_counts.get(row.get("status", ""), 0) + 1

    report = {
        "run_timestamp": utc_now(),
        "input_csv": args.input_csv or str(LIFECYCLE_CSV.relative_to(ROOT)),
        "removal_statuses": sorted(part.strip() for part in args.removal_statuses.split(",") if part.strip()),
        "metric_statuses": sorted(part.strip() for part in args.metric_statuses.split(",") if part.strip()),
        "targeted_games": len(catalog),
        "games_in_scope": len(scope),
        "fresh_statuses_skipped": fresh_skipped,
        "pending_before_run": len(pending),
        "attempted_this_run": len(selected),
        "available_this_run": counts["available"],
        "unavailable_this_run": counts["unavailable"],
        "failed_this_run": counts["failed"],
        "live_page_status_entries": len(statuses),
        "status_counts": dict(sorted(status_counts.items())),
        "outputs": {
            "csv": str(STATUS_CSV.relative_to(ROOT)),
            "json": str(STATUS_EXPORT_JSON.relative_to(ROOT)),
            "raw_status_json": str(STATUS_JSON.relative_to(ROOT)),
            "report_json": str(REPORT_JSON.relative_to(ROOT)),
            "report_md": str(REPORT_MD.relative_to(ROOT)),
        },
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Kongregate Live Game Page Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- Targeted games: {report['targeted_games']}",
                f"- Games in scope: {report['games_in_scope']}",
                f"- Fresh statuses skipped: {report['fresh_statuses_skipped']}",
                f"- Pending before run: {report['pending_before_run']}",
                f"- Attempted this run: {report['attempted_this_run']}",
                f"- Available this run: {report['available_this_run']}",
                f"- Unavailable this run: {report['unavailable_this_run']}",
                f"- Failed this run: {report['failed_this_run']}",
                f"- Live page status entries: {report['live_page_status_entries']}",
                f"- Status counts: {report['status_counts']}",
                "",
                "## Outputs",
                "",
                f"- `{report['outputs']['csv']}`",
                f"- `{report['outputs']['json']}`",
                "",
            ]
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
