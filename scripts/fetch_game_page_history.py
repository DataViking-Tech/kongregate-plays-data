#!/usr/bin/env python3
"""Fetch archived Kongregate game pages and extract explicit play counts."""

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
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path

from kongregate_canonical import canonical_game_url as shared_canonical_game_url


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_GAME_PAGES = ROOT / "data" / "raw" / "game_pages"
RAW_CDX = RAW_GAME_PAGES / "cdx"
RAW_HTML = RAW_GAME_PAGES / "html"
LOGS = ROOT / "logs"

CATALOG_CSV = PROCESSED / "mini_catalog.csv"
PROFILE_CSV = PROCESSED / "metrics_no_cdx_profile.csv"
MANIFEST_PATH = RAW_GAME_PAGES / "manifest.json"
FAILURE_PATH = RAW_GAME_PAGES / "failures.json"
REPORT_JSON = LOGS / "game_page_history_report.json"
REPORT_MD = LOGS / "game_page_history_report.md"
ERROR_LOG = LOGS / "game_page_history_errors.log"

CDX_ENDPOINT = "https://web.archive.org/cdx"
WAYBACK_RAW = "https://web.archive.org/web/{timestamp}id_/{original}"
CDX_FIELDS = ["timestamp", "original", "statuscode", "mimetype", "digest", "length"]


@dataclass(frozen=True)
class ProfileGame:
    game_url: str
    game_name: str
    canonical_key: str
    tier: int
    priority_score: int
    best_rank: int
    top_n_appearances: int
    listing_play_count_rows: int
    first_seen_date: str
    last_seen_date: str
    game_url_variants: tuple[str, ...]


@dataclass(frozen=True)
class GamePageJob:
    game_url: str
    game_name: str
    canonical_key: str
    tier: int
    priority_score: int
    best_rank: int
    first_seen_date: str
    last_seen_date: str
    timestamp: str
    original: str
    digest: str
    mimetype: str
    length: str


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def parse_int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value or "")
    match = re.search(r"\d[\d,]*", text)
    if not match:
        return 0
    return int(match.group(0).replace(",", ""))


def parse_iso_date(value: str):
    text = str(value or "")[:10]
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_timestamp_date(timestamp: str):
    text = str(timestamp or "")[:8]
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None


def ranked_window_distance(job: GamePageJob) -> int:
    capture_date = parse_timestamp_date(job.timestamp)
    first_seen = parse_iso_date(job.first_seen_date)
    last_seen = parse_iso_date(job.last_seen_date)
    if not capture_date or not first_seen:
        return 0
    last_seen = last_seen or first_seen
    if first_seen <= capture_date <= last_seen:
        return 0
    return min(abs((capture_date - first_seen).days), abs((capture_date - last_seen).days))


def canonical_game_url(game_url: str) -> str:
    return shared_canonical_game_url(game_url)


def game_url_parts(game_url: str) -> tuple[str, str] | None:
    if not game_url:
        return None
    parsed = urllib.parse.urlsplit(game_url)
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/]+)", parsed.path)
    if not match:
        return None
    return urllib.parse.unquote(match.group(1)), urllib.parse.unquote(match.group(2))


def load_catalog_variants() -> dict[str, tuple[str, ...]]:
    variants_by_key: dict[str, list[str]] = {}
    if not CATALOG_CSV.exists():
        return {}
    with CATALOG_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = canonical_game_url(row.get("game_url", ""))
            if not key:
                continue
            variants = variants_by_key.setdefault(key, [])
            for value in [row.get("game_url", ""), *row.get("game_url_variants", "").split(";")]:
                value = value.strip()
                if value and value not in variants:
                    variants.append(value)
    return {key: tuple(values) for key, values in variants_by_key.items()}


def page_url_variants(game_url: str, catalog_variants: tuple[str, ...]) -> tuple[str, ...]:
    variants: list[str] = []
    for value in [game_url, *catalog_variants]:
        value = value.strip()
        if value and value not in variants:
            variants.append(value)
        parts = game_url_parts(value)
        if not parts:
            continue
        developer, slug = parts
        generated = [
            f"http://www.kongregate.com/games/{developer}/{slug}",
            f"http://www.kongregate.com:80/games/{developer}/{slug}",
            f"http://kongregate.com/games/{developer}/{slug}",
            f"http://kongregate.com:80/games/{developer}/{slug}",
            f"https://www.kongregate.com/games/{developer}/{slug}",
            f"https://www.kongregate.com/en/games/{developer}/{slug}",
        ]
        for candidate in generated:
            if candidate not in variants:
                variants.append(candidate)
    return tuple(variants)


def load_profile_games(profile_csv: Path, tiers: set[int]) -> list[ProfileGame]:
    catalog_variants = load_catalog_variants()
    games: list[ProfileGame] = []
    with profile_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            tier = parse_int(row.get("followup_tier"))
            if not tier:
                need = str(row.get("needs_game_page_history", "")).strip().lower()
                if need == "yes":
                    tier = 1
                elif need == "partial":
                    tier = 2
                else:
                    tier = 3
            if tiers and tier not in tiers:
                continue
            game_url = row.get("game_url", "")
            canonical_key = row.get("canonical_game_key") or canonical_game_url(game_url)
            games.append(
                ProfileGame(
                    game_url=game_url,
                    game_name=row.get("game_name", ""),
                    canonical_key=canonical_key,
                    tier=tier,
                    priority_score=parse_int(row.get("priority_score")),
                    best_rank=parse_int(row.get("best_rank")),
                    top_n_appearances=parse_int(row.get("top_n_appearances")),
                    listing_play_count_rows=parse_int(row.get("listing_play_count_rows")),
                    first_seen_date=row.get("first_seen_date", ""),
                    last_seen_date=row.get("last_seen_date", ""),
                    game_url_variants=page_url_variants(game_url, catalog_variants.get(canonical_key, ())),
                )
            )
    games.sort(
        key=lambda game: (
            game.tier,
            -game.priority_score,
            game.best_rank or 999999,
            -game.listing_play_count_rows,
            -game.top_n_appearances,
            game.first_seen_date,
            game.game_name.lower(),
        )
    )
    return games


def cdx_cache_path(page_url: str) -> Path:
    return RAW_CDX / f"{safe_name(page_url)}_{sha(page_url)}.json"


def cdx_query_url(page_url: str, collapse: str) -> str:
    params = [
        ("url", page_url),
        ("output", "json"),
        ("fl", ",".join(CDX_FIELDS)),
        ("filter", "statuscode:200"),
        ("filter", "mimetype:text/html"),
    ]
    if collapse:
        params.append(("collapse", collapse))
    return f"{CDX_ENDPOINT}?{urllib.parse.urlencode(params)}"


def fetch_cdx(
    page_url: str,
    timeout_s: int,
    collapse: str,
    refresh: bool,
    retries: int,
    retry_sleep_s: float,
    cached_only: bool,
) -> tuple[list[dict[str, str]], str]:
    RAW_CDX.mkdir(parents=True, exist_ok=True)
    cache_path = cdx_cache_path(page_url)
    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text()), "cached"
    if cached_only and not refresh:
        return [], "missing_cache_skipped"

    request = urllib.request.Request(cdx_query_url(page_url, collapse), headers={"User-Agent": "KongregateGamePageHistory/0.1"})
    last_error = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
            break
        except (TimeoutError, socket.timeout, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            if attempt < retries:
                time.sleep(retry_sleep_s * (attempt + 1))
    else:
        ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\tcdx\t{page_url}\t{last_error}\n")
        return [], f"failed: {last_error}"

    headers = data[0] if data else CDX_FIELDS
    rows = [dict(zip(headers, row)) for row in data[1:]] if len(data) > 1 else []
    cache_path.write_text(json.dumps(rows, indent=2, sort_keys=True))
    return rows, "fetched"


def build_jobs(
    games: list[ProfileGame],
    timeout_s: int,
    cdx_sleep_s: float,
    refresh_cdx: bool,
    max_cdx_games: int,
    variant_limit: int,
    collapse: str,
    cdx_retries: int,
    cdx_retry_sleep_s: float,
    cached_cdx_only: bool,
) -> tuple[list[GamePageJob], dict[str, int]]:
    jobs: list[GamePageJob] = []
    stats = {
        "cdx_games_considered": 0,
        "cdx_urls_fetched": 0,
        "cdx_urls_cached": 0,
        "cdx_urls_failed": 0,
        "cdx_urls_missing_cache_skipped": 0,
        "cdx_rows": 0,
    }
    for game in games:
        if max_cdx_games and stats["cdx_games_considered"] >= max_cdx_games:
            break
        stats["cdx_games_considered"] += 1
        variants = game.game_url_variants[:variant_limit] if variant_limit else game.game_url_variants
        for page_url in variants:
            rows, status = fetch_cdx(
                page_url,
                timeout_s=timeout_s,
                collapse=collapse,
                refresh=refresh_cdx,
                retries=cdx_retries,
                retry_sleep_s=cdx_retry_sleep_s,
                cached_only=cached_cdx_only,
            )
            if status == "cached":
                stats["cdx_urls_cached"] += 1
            elif status == "fetched":
                stats["cdx_urls_fetched"] += 1
            elif status == "missing_cache_skipped":
                stats["cdx_urls_missing_cache_skipped"] += 1
            else:
                stats["cdx_urls_failed"] += 1
            if status != "cached":
                time.sleep(cdx_sleep_s)
            stats["cdx_rows"] += len(rows)
            for row in rows:
                jobs.append(
                    GamePageJob(
                        game_url=game.game_url,
                        game_name=game.game_name,
                        canonical_key=game.canonical_key,
                        tier=game.tier,
                        priority_score=game.priority_score,
                        best_rank=game.best_rank,
                        first_seen_date=game.first_seen_date,
                        last_seen_date=game.last_seen_date,
                        timestamp=row.get("timestamp", ""),
                        original=row.get("original", page_url),
                        digest=row.get("digest", ""),
                        mimetype=row.get("mimetype", ""),
                        length=row.get("length", ""),
                    )
                )

    deduped: dict[tuple[str, str, str], GamePageJob] = {}
    for job in jobs:
        if job.timestamp and job.original:
            deduped[(job.canonical_key, job.timestamp, job.original)] = job
    return sorted(
        deduped.values(),
        key=lambda job: (
            job.tier,
            -job.priority_score,
            job.best_rank or 999999,
            ranked_window_distance(job),
            job.game_name.lower(),
            job.timestamp,
            job.original,
        ),
    ), stats


def html_cache_path(job: GamePageJob) -> Path:
    digest = sha(f"{job.timestamp}:{job.original}")
    return RAW_HTML / f"{job.timestamp}_{safe_name(job.original)}_{digest}.html"


def decode_payload(payload: bytes, headers) -> str:
    if payload[:2] == b"\x1f\x8b" or str(headers.get("Content-Encoding", "")).lower() == "gzip":
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass
    return payload.decode("utf-8", errors="replace")


def strip_html(markup: str) -> str:
    markup = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", markup)
    text = re.sub(r"(?s)<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def snippet_around(markup: str, pattern: str, before: int = 400, after: int = 1600) -> list[str]:
    snippets = []
    for match in re.finditer(pattern, markup, flags=re.IGNORECASE):
        start = max(0, match.start() - before)
        end = min(len(markup), match.end() + after)
        snippets.append(markup[start:end])
    return snippets


def parse_game_page_counts(markup: str) -> dict[str, object] | None:
    for snippet in snippet_around(markup, r"id=[\"']favorite_game[\"']"):
        text = strip_html(snippet)
        match = re.search(r"Favorited\s+(\d[\d,]*)\s+times\s+(\d[\d,]*)\s+(?:gameplays|plays)\b", text, flags=re.IGNORECASE)
        if match:
            favorites_text, plays_text = match.groups()
            return {
                "plays": parse_int(plays_text),
                "favorites": parse_int(favorites_text),
                "plays_text": plays_text,
                "favorites_text": favorites_text,
                "confidence": "high",
                "parser_detail": "favorite_game_block",
            }

    span_patterns = [
        r"<span[^>]*class=[\"'][^\"']*\bgameplays_count\b[^\"']*[\"'][^>]*>\s*(\d[\d,]*)\s*</span>",
        r"<[^>]+class=[\"'][^\"']*\bgameplays\b[^\"']*[\"'][^>]*>\s*(\d[\d,]*)\s*(?:gameplays|plays)\b",
    ]
    for pattern in span_patterns:
        match = re.search(pattern, markup, flags=re.IGNORECASE)
        if match:
            plays_text = match.group(1)
            return {
                "plays": parse_int(plays_text),
                "favorites": 0,
                "plays_text": plays_text,
                "favorites_text": "",
                "confidence": "medium_high",
                "parser_detail": "filled_gameplays_count",
            }

    return None


def fetch_page(job: GamePageJob, timeout_s: int, retries: int, retry_sleep_s: float) -> tuple[bool, str, dict[str, object] | None]:
    target = html_cache_path(job)
    if target.exists() and target.stat().st_size > 0:
        markup = target.read_text(errors="replace")
    else:
        request = urllib.request.Request(
            WAYBACK_RAW.format(timestamp=job.timestamp, original=job.original),
            headers={"User-Agent": "KongregateGamePageHistory/0.1", "Accept": "text/html,*/*"},
        )
        markup = ""
        last_error = ""
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=timeout_s) as response:
                    markup = decode_payload(response.read(), response.headers)
                break
            except urllib.error.HTTPError as exc:
                markup = decode_payload(exc.read(), exc.headers)
                if exc.code < 500:
                    break
                last_error = f"http_{exc.code}"
            except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
                last_error = str(exc)
            if attempt < retries:
                time.sleep(retry_sleep_s * (attempt + 1))
        else:
            return False, last_error or "request_failed", None

        if not markup:
            return False, last_error or "empty", None
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markup, encoding="utf-8")

    parsed = parse_game_page_counts(markup)
    if not parsed or not parse_int(parsed.get("plays")):
        return False, "no_explicit_count", None
    return True, str(target.relative_to(ROOT)), parsed


def make_report(
    args,
    profile_csv: Path,
    tiers: set[int],
    games: list[ProfileGame],
    cdx_stats: dict[str, int],
    jobs_count: int,
    pending_count: int,
    selected_count: int,
    fetched: int,
    cached_selected: int,
    parsed_rows: int,
    failed: int,
    no_explicit_count: int,
    manifest: dict[str, dict[str, object]],
    failures: dict[str, dict[str, object]],
    history_rows: list[dict[str, object]],
) -> dict[str, object]:
    game_page_history_rows = sum(1 for row in history_rows if row.get("parser") == "game_page_html")
    selected_profile_games = [
        {
            "game_name": game.game_name,
            "game_url": game.game_url,
            "canonical_game_key": game.canonical_key,
            "tier": game.tier,
            "priority_score": game.priority_score,
            "best_rank": game.best_rank,
            "top_n_appearances": game.top_n_appearances,
            "listing_play_count_rows": game.listing_play_count_rows,
            "first_seen_date": game.first_seen_date,
            "last_seen_date": game.last_seen_date,
        }
        for game in games
    ]
    return {
        "run_timestamp": utc_now(),
        "input_csv": str(profile_csv.relative_to(ROOT)) if profile_csv.is_relative_to(ROOT) else str(profile_csv),
        "tiers": sorted(tiers),
        "profile_games_in_scope": len(games),
        "selected_profile_games": selected_profile_games,
        "profile_offset": args.profile_offset,
        "profile_limit": args.profile_limit,
        "max_cdx_games": args.max_cdx_games,
        "variant_limit": args.variant_limit,
        "max_fetches": args.max_fetches,
        "max_jobs_per_game": args.max_jobs_per_game,
        "collapse": args.collapse,
        "timeout": args.timeout,
        "cdx_timeout": args.cdx_timeout or args.timeout,
        "cached_cdx_only": args.cached_cdx_only,
        "game_name_contains": args.game_name_contains,
        "retry_failures": args.retry_failures,
        "report_only": args.report_only,
        **cdx_stats,
        "page_jobs": jobs_count,
        "pending_before_run": pending_count,
        "attempted_this_run": selected_count,
        "fetched_this_run": fetched,
        "cached_selected_this_run": cached_selected,
        "parsed_rows_this_run": parsed_rows,
        "failed_this_run": failed,
        "no_explicit_count_this_run": no_explicit_count,
        "manifest_entries": len(manifest),
        "known_failures": len(failures),
        "history_rows": len(history_rows),
        "game_page_history_rows": game_page_history_rows,
        "outputs": {
            "manifest": str(MANIFEST_PATH.relative_to(ROOT)),
            "failures": str(FAILURE_PATH.relative_to(ROOT)),
            "history_csv": "data/processed/game_play_history.csv",
            "report_json": str(REPORT_JSON.relative_to(ROOT)),
            "report_md": str(REPORT_MD.relative_to(ROOT)),
        },
    }


def write_report(report: dict[str, object]) -> None:
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Kongregate Game Page History Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- Profile games in scope: {report['profile_games_in_scope']}",
                f"- Selected games: {', '.join(game['game_name'] for game in report.get('selected_profile_games', [])) or 'none'}",
                f"- CDX games considered: {report['cdx_games_considered']}",
                f"- Cached CDX only: {report['cached_cdx_only']}",
                f"- CDX timeout: {report['cdx_timeout']}s",
                f"- Page timeout: {report['timeout']}s",
                f"- Game-name filter: {report['game_name_contains'] or 'none'}",
                f"- CDX rows: {report['cdx_rows']}",
                f"- Page jobs: {report['page_jobs']}",
                f"- Pending before run: {report['pending_before_run']}",
                f"- Attempted this run: {report['attempted_this_run']}",
                f"- Fetched this run: {report['fetched_this_run']}",
                f"- Parsed rows this run: {report['parsed_rows_this_run']}",
                f"- No explicit count this run: {report['no_explicit_count_this_run']}",
                f"- Failed this run: {report['failed_this_run']}",
                f"- Manifest entries: {report['manifest_entries']}",
                f"- Known failures: {report['known_failures']}",
                f"- Combined history rows: {report['history_rows']}",
                f"- Game-page history rows: {report['game_page_history_rows']}",
                f"- Report only: {report['report_only']}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch archived game-page histories for no-CDX metrics gaps.")
    parser.add_argument("--input-csv", default=str(PROFILE_CSV), help="No-CDX profile CSV to target.")
    parser.add_argument("--tiers", default="1", help="Comma-separated follow-up tiers to target. Empty means all.")
    parser.add_argument("--profile-offset", type=int, default=0, help="Skip this many sorted profile games before CDX lookup. Useful for resumable broad sweeps.")
    parser.add_argument("--profile-limit", type=int, default=0, help="Limit sorted profile games after --profile-offset. 0 means no profile slice limit.")
    parser.add_argument("--max-cdx-games", type=int, default=0, help="Limit profile games to check for CDX rows. 0 means all.")
    parser.add_argument("--variant-limit", type=int, default=0, help="Limit URL variants queried per game. 0 means all variants.")
    parser.add_argument("--max-fetches", type=int, default=0, help="Limit archived page fetch/parse attempts. 0 means all pending.")
    parser.add_argument("--max-jobs-per-game", type=int, default=0, help="Limit selected page fetch/parse jobs per canonical game in this run. 0 means no per-game cap.")
    parser.add_argument("--collapse", default="digest", help="Optional CDX collapse value. Default digest keeps unique page revisions.")
    parser.add_argument("--timeout", type=int, default=25, help="Per-request timeout in seconds.")
    parser.add_argument("--cdx-timeout", type=int, default=0, help="Per-request timeout for CDX lookups. Defaults to --timeout when omitted.")
    parser.add_argument("--sleep", type=float, default=0.5, help="Seconds to sleep after an archived page fetch.")
    parser.add_argument("--cdx-sleep", type=float, default=0.8, help="Seconds to sleep after a fresh CDX lookup.")
    parser.add_argument("--cdx-retries", type=int, default=2, help="Retries for transient CDX lookup failures.")
    parser.add_argument("--cdx-retry-sleep", type=float, default=2.0, help="Initial seconds to back off between CDX retries.")
    parser.add_argument("--page-retries", type=int, default=2, help="Retries for transient archived page fetch failures.")
    parser.add_argument("--retry-sleep", type=float, default=1.5, help="Initial seconds to back off between page retries.")
    parser.add_argument("--refresh-cdx", action="store_true", help="Refresh cached CDX responses.")
    parser.add_argument("--cached-cdx-only", action="store_true", help="Use only existing CDX cache files; skip uncached CDX lookups.")
    parser.add_argument("--retry-failures", action="store_true", help="Retry previously failed page captures.")
    parser.add_argument("--report-only", action="store_true", help="Rewrite reports from current manifests without network work.")
    parser.add_argument("--game-name-contains", default="", help="Comma-separated case-insensitive substrings to target by game name or URL.")
    args = parser.parse_args()

    profile_csv = Path(args.input_csv)
    tiers = {parse_int(value) for value in args.tiers.split(",") if value.strip()}
    for directory in (RAW_CDX, RAW_HTML, PROCESSED, LOGS):
        directory.mkdir(parents=True, exist_ok=True)

    games = load_profile_games(profile_csv, tiers)
    name_filters = [value.strip().lower() for value in args.game_name_contains.split(",") if value.strip()]
    if name_filters:
        games = [
            game
            for game in games
            if any(value in game.game_name.lower() or value in game.game_url.lower() for value in name_filters)
        ]
    if args.profile_offset:
        games = games[args.profile_offset :]
    if args.profile_limit:
        games = games[: args.profile_limit]
    manifest = read_json(MANIFEST_PATH, {})
    failures = read_json(FAILURE_PATH, {})
    if args.report_only:
        from rebuild_game_play_history import rebuild_history, write_history

        history_rows = rebuild_history()
        write_history(history_rows)
        report = make_report(
            args,
            profile_csv,
            tiers,
            games,
            {"cdx_games_considered": 0, "cdx_urls_fetched": 0, "cdx_urls_cached": 0, "cdx_urls_failed": 0, "cdx_urls_missing_cache_skipped": 0, "cdx_rows": 0},
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            manifest,
            failures,
            history_rows,
        )
        write_report(report)
        print(json.dumps(report, indent=2))
        return

    jobs, cdx_stats = build_jobs(
        games,
        timeout_s=args.cdx_timeout or args.timeout,
        cdx_sleep_s=args.cdx_sleep,
        refresh_cdx=args.refresh_cdx,
        max_cdx_games=args.max_cdx_games,
        variant_limit=args.variant_limit,
        collapse=args.collapse,
        cdx_retries=args.cdx_retries,
        cdx_retry_sleep_s=args.cdx_retry_sleep,
        cached_cdx_only=args.cached_cdx_only,
    )

    def job_needs_fetch_or_parse(job: GamePageJob) -> bool:
        relative = str(html_cache_path(job).relative_to(ROOT))
        failure_key = f"{job.canonical_key}\t{job.timestamp}\t{job.original}"
        if relative in manifest:
            return False
        return args.retry_failures or failure_key not in failures

    pending = [job for job in jobs if job_needs_fetch_or_parse(job)]

    selected = []
    selected_by_game: dict[str, int] = defaultdict(int)
    for job in pending:
        if args.max_fetches and len(selected) >= args.max_fetches:
            break
        if args.max_jobs_per_game and selected_by_game[job.canonical_key] >= args.max_jobs_per_game:
            continue
        selected.append(job)
        selected_by_game[job.canonical_key] += 1

    fetched = 0
    cached_selected = 0
    parsed_rows = 0
    failed = 0
    no_explicit_count = 0
    for job in selected:
        target = html_cache_path(job)
        was_cached = target.exists() and target.stat().st_size > 0
        ok, detail, parsed = fetch_page(job, args.timeout, args.page_retries, args.retry_sleep)
        failure_key = f"{job.canonical_key}\t{job.timestamp}\t{job.original}"
        if ok and parsed:
            if was_cached:
                cached_selected += 1
            else:
                fetched += 1
            parsed_rows += 1
            relative = str(target.relative_to(ROOT))
            manifest[relative] = {
                "game_url": job.game_url,
                "game_name": job.game_name,
                "canonical_game_key": job.canonical_key,
                "followup_tier": job.tier,
                "capture_timestamp": job.timestamp,
                "original_url": job.original,
                "digest": job.digest,
                "mimetype": job.mimetype,
                "length": job.length,
                "plays_count_observed": int(parsed["plays"]),
                "favorites_count_observed": int(parsed.get("favorites") or 0),
                "plays_text": str(parsed.get("plays_text") or parsed["plays"]),
                "favorites_text": str(parsed.get("favorites_text") or ""),
                "confidence": str(parsed.get("confidence") or "high"),
                "parser_detail": str(parsed.get("parser_detail") or ""),
                "notes": f"Extracted from archived game page HTML {relative}",
            }
            failures.pop(failure_key, None)
        else:
            failed += 1
            if detail == "no_explicit_count":
                no_explicit_count += 1
            failures[failure_key] = {
                "game_url": job.game_url,
                "game_name": job.game_name,
                "canonical_game_key": job.canonical_key,
                "capture_timestamp": job.timestamp,
                "original_url": job.original,
                "last_error": detail,
                "last_attempt_timestamp": utc_now(),
                "cached_html": str(target.relative_to(ROOT)) if target.exists() else "",
            }
            ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\thtml\t{job.timestamp}\t{job.original}\t{job.game_url}\t{detail}\n")
        write_json(MANIFEST_PATH, manifest)
        write_json(FAILURE_PATH, failures)
        time.sleep(args.sleep)

    write_json(MANIFEST_PATH, manifest)
    write_json(FAILURE_PATH, failures)

    from rebuild_game_play_history import rebuild_history, write_history

    history_rows = rebuild_history()
    write_history(history_rows)
    report = make_report(
        args,
        profile_csv,
        tiers,
        games,
        cdx_stats,
        len(jobs),
        len(pending),
        len(selected),
        fetched,
        cached_selected,
        parsed_rows,
        failed,
        no_explicit_count,
        manifest,
        failures,
        history_rows,
    )
    write_report(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
