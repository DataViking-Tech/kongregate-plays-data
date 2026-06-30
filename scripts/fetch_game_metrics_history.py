#!/usr/bin/env python3
"""Fetch archived Kongregate per-game metrics histories for the mini catalog."""

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


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
RAW_CDX = RAW / "cdx" / "game_metrics"
RAW_METRICS = RAW / "game_metrics"
RAW_METRICS_JSON = RAW_METRICS / "json"
LOGS = ROOT / "logs"

CATALOG_CSV = PROCESSED / "mini_catalog.csv"
HISTORY_CSV = PROCESSED / "game_play_history.csv"
HISTORY_JSON = PROCESSED / "game_play_history.json"
AUDIT_CSV = PROCESSED / "metrics_backfill_gap_audit.csv"
MANIFEST_PATH = RAW_METRICS / "manifest.json"
FAILURE_PATH = RAW_METRICS / "failures.json"
REPORT_JSON = LOGS / "game_metrics_history_report.json"
REPORT_MD = LOGS / "game_metrics_history_report.md"
ERROR_LOG = LOGS / "game_metrics_history_errors.log"

CDX_ENDPOINT = "https://web.archive.org/cdx"
WAYBACK_RAW = "https://web.archive.org/web/{timestamp}id_/{original}"
WAYBACK_VIEW = "https://web.archive.org/web/{timestamp}/{original}"
CDX_FIELDS = ["timestamp", "original", "statuscode", "mimetype", "digest", "length"]

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


@dataclass(frozen=True)
class CatalogGame:
    catalog_index: int
    game_url: str
    game_name: str
    game_url_variants: tuple[str, ...]


@dataclass(frozen=True)
class MetricsJob:
    catalog_index: int
    game_url: str
    game_name: str
    timestamp: str
    original: str
    digest: str
    mimetype: str
    length: str


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_name(text: str) -> str:
    text = urllib.parse.unquote(text)
    text = text.replace("?sort=", "_sort_")
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


def load_catalog() -> list[CatalogGame]:
    rows = list(csv.DictReader(CATALOG_CSV.open(newline="", encoding="utf-8")))
    games = [
        CatalogGame(
            catalog_index=index,
            game_url=row["game_url"],
            game_name=row["game_name"],
            game_url_variants=game_url_variants(row),
        )
        for index, row in enumerate(rows)
        if row.get("game_url")
    ]
    return games


def game_url_variants(row: dict[str, str]) -> tuple[str, ...]:
    variants = []
    if row.get("game_url"):
        variants.append(row["game_url"])
    variants.extend(part.strip() for part in row.get("game_url_variants", "").split(";") if part.strip())
    return tuple(dict.fromkeys(variants))


def canonical_game_url(game_url: str) -> str:
    if not game_url:
        return ""
    parsed = urllib.parse.urlsplit(game_url)
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/]+)", parsed.path)
    if not match:
        return game_url.lower()
    developer, slug = match.groups()
    return f"www.kongregate.com/games/{urllib.parse.unquote(developer)}/{urllib.parse.unquote(slug)}".lower()


def load_audit_rows() -> dict[str, dict[str, str]]:
    rows = {}
    if not AUDIT_CSV.exists():
        return rows
    with AUDIT_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = canonical_game_url(row.get("game_url", ""))
            if key:
                rows[key] = row
    return rows


def audit_int(row: dict[str, str] | None, key: str) -> int:
    if not row:
        return 0
    value = parse_int(row.get(key))
    return value if isinstance(value, int) else 0


def metric_cdx_keys_for_game(game_url: str) -> list[str]:
    parsed = urllib.parse.urlsplit(game_url)
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/]+)/?$", parsed.path)
    if not match:
        return []
    developer, slug = match.groups()
    paths = [f"www.kongregate.com/games/{developer}/{slug}/metrics.json"]
    if parsed.path.startswith("/en/games/"):
        paths.append(f"www.kongregate.com/en/games/{developer}/{slug}/metrics.json")
    return list(dict.fromkeys(paths))


def cdx_cache_path(metrics_url: str) -> Path:
    return RAW_CDX / f"{safe_name(metrics_url)}_{sha(metrics_url)}.json"


def cdx_query_url(metrics_url: str, collapse: str) -> str:
    params = [
        ("url", metrics_url),
        ("matchType", "exact"),
        ("output", "json"),
        ("fl", ",".join(CDX_FIELDS)),
        ("filter", "statuscode:200"),
        ("filter", "mimetype:application/json"),
    ]
    if collapse:
        params.append(("collapse", collapse))
    return f"{CDX_ENDPOINT}?{urllib.parse.urlencode(params)}"


def row_scheme(original: str) -> str:
    return urllib.parse.urlsplit(original).scheme.lower()


def fetch_cdx(metrics_url: str, timeout_s: int, collapse: str, refresh: bool, retries: int, retry_sleep_s: float) -> tuple[list[dict[str, str]], str]:
    RAW_CDX.mkdir(parents=True, exist_ok=True)
    cache_path = cdx_cache_path(metrics_url)
    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text()), "cached"

    request = urllib.request.Request(cdx_query_url(metrics_url, collapse), headers={"User-Agent": "KongregateGameMetricsHistory/0.1"})
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
        ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\tcdx\t{metrics_url}\t{last_error}\n")
        return [], f"failed: {last_error}"

    headers = data[0] if data else CDX_FIELDS
    rows = [dict(zip(headers, row)) for row in data[1:]] if len(data) > 1 else []
    cache_path.write_text(json.dumps(rows, indent=2, sort_keys=True))
    return rows, "fetched"


def load_cdx(
    metrics_url: str,
    timeout_s: int,
    collapse: str,
    refresh: bool,
    retries: int,
    retry_sleep_s: float,
    cached_only: bool,
) -> tuple[list[dict[str, str]], str]:
    cache_path = cdx_cache_path(metrics_url)
    if cached_only and not refresh and not cache_path.exists():
        return [], "missing_cache_skipped"
    return fetch_cdx(metrics_url, timeout_s, collapse, refresh, retries, retry_sleep_s)


def metrics_cache_path(job: MetricsJob) -> Path:
    digest = sha(f"{job.timestamp}:{job.original}")
    return RAW_METRICS_JSON / f"{job.timestamp}_{safe_name(job.original)}_{digest}.json"


def decode_payload(payload: bytes, headers) -> str:
    if payload[:2] == b"\x1f\x8b" or str(headers.get("Content-Encoding", "")).lower() == "gzip":
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass
    return payload.decode("utf-8", errors="replace")


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


def metrics_json_is_valid(path: Path) -> bool:
    if not path.exists() or path.stat().st_size <= 0:
        return False
    try:
        payload = json.loads(path.read_text(errors="replace"))
    except json.JSONDecodeError:
        return False
    return bool(parse_int(payload.get("gameplays_count") or payload.get("gameplays_count_with_delimiter")))


def fetch_metrics(job: MetricsJob, timeout_s: int, retries: int, retry_sleep_s: float) -> tuple[bool, str]:
    target = metrics_cache_path(job)
    if metrics_json_is_valid(target):
        return True, "cached"

    request = urllib.request.Request(
        WAYBACK_RAW.format(timestamp=job.timestamp, original=job.original),
        headers={"User-Agent": "KongregateGameMetricsHistory/0.1", "Accept": "application/json,text/plain,*/*"},
    )
    payload = ""
    last_error = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                payload = decode_payload(response.read(), response.headers)
            break
        except urllib.error.HTTPError as exc:
            payload = decode_payload(exc.read(), exc.headers)
            if exc.code < 500:
                break
            last_error = f"http_{exc.code}"
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            last_error = str(exc)
        if attempt < retries:
            time.sleep(retry_sleep_s * (attempt + 1))
    else:
        return False, last_error or "request_failed"

    if not payload:
        return False, last_error or "empty"

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return False, "not_json"
    if not parse_int(parsed.get("gameplays_count") or parsed.get("gameplays_count_with_delimiter")):
        return False, "no_gameplays_count"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(parsed, indent=2, sort_keys=True))
    return True, str(target.relative_to(ROOT))


def load_manifest() -> dict[str, dict[str, str]]:
    return read_json(MANIFEST_PATH, {})


def load_failures() -> dict[str, dict[str, str]]:
    return read_json(FAILURE_PATH, {})


def build_jobs(
    games: list[CatalogGame],
    schemes: set[str],
    timeout_s: int,
    cdx_sleep_s: float,
    refresh_cdx: bool,
    max_cdx_games: int,
    collapse: str,
    cdx_retries: int,
    cdx_retry_sleep_s: float,
    cached_cdx_only: bool,
) -> tuple[list[MetricsJob], dict[str, int]]:
    jobs: list[MetricsJob] = []
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
        metrics_urls = []
        for game_url_variant in game.game_url_variants:
            metrics_urls.extend(metric_cdx_keys_for_game(game_url_variant))
        for metrics_url in dict.fromkeys(metrics_urls):
            rows, status = load_cdx(
                metrics_url,
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
            if status not in {"cached", "missing_cache_skipped"}:
                time.sleep(cdx_sleep_s)
            rows = [row for row in rows if not schemes or row_scheme(row.get("original", "")) in schemes]
            stats["cdx_rows"] += len(rows)
            for row in rows:
                jobs.append(
                    MetricsJob(
                        catalog_index=game.catalog_index,
                        game_url=game.game_url,
                        game_name=game.game_name,
                        timestamp=row.get("timestamp", ""),
                        original=row.get("original", metrics_url),
                        digest=row.get("digest", ""),
                        mimetype=row.get("mimetype", ""),
                        length=row.get("length", ""),
                    )
                )

    deduped: dict[tuple[str, str, str], MetricsJob] = {}
    for job in jobs:
        if job.timestamp and job.original:
            deduped[(job.game_url, job.timestamp, job.original)] = job
    return sorted(deduped.values(), key=lambda job: (job.catalog_index, job.timestamp, job.original)), stats


def rebuild_history(manifest: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    seen = set()
    for relative_path, meta in sorted(manifest.items()):
        path = ROOT / relative_path
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(errors="replace"))
        except json.JSONDecodeError:
            continue
        plays = parse_int(payload.get("gameplays_count") or payload.get("gameplays_count_with_delimiter"))
        if not plays:
            continue
        favorites = parse_int(payload.get("favorites_count") or payload.get("favorites_count_with_delimiter"))
        key = (meta.get("game_url", ""), meta.get("capture_timestamp", ""), plays)
        if key in seen:
            continue
        seen.add(key)
        timestamp = meta.get("capture_timestamp", "")
        rows.append(
            {
                "date": datetime.strptime(timestamp[:8], "%Y%m%d").date().isoformat() if len(timestamp) >= 8 else "",
                "game_name": meta.get("game_name", ""),
                "game_url": meta.get("game_url", ""),
                "plays_count_observed": plays,
                "favorites_count_observed": favorites,
                "plays_text": payload.get("gameplays_count_with_delimiter", str(plays)),
                "favorites_text": payload.get("favorites_count_with_delimiter", str(favorites) if favorites else ""),
                "metrics_url": meta.get("original_url", ""),
                "capture_timestamp": timestamp,
                "capture_url": WAYBACK_VIEW.format(timestamp=timestamp, original=meta.get("original_url", "")),
                "parser": "metrics_json",
                "confidence": "high",
                "notes": f"Extracted from archived game metrics JSON {relative_path}",
            }
        )
    rows.sort(key=lambda row: (row["date"], row["game_name"].lower(), row["capture_timestamp"]))
    return rows


def write_history(rows: list[dict[str, object]]) -> None:
    with HISTORY_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    HISTORY_JSON.write_text(json.dumps({"columns": HISTORY_COLUMNS, "rows": rows}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch archived metrics.json histories for games in the Kongregate mini catalog.")
    parser.add_argument("--max-cdx-games", type=int, default=0, help="Limit catalog games to check for CDX rows this run. 0 means all.")
    parser.add_argument("--catalog-offset", type=int, default=0, help="Skip this many catalog rows before CDX discovery.")
    parser.add_argument("--catalog-limit", type=int, default=0, help="Limit catalog rows after --catalog-offset. 0 means all remaining rows.")
    parser.add_argument("--audit-statuses", default="", help="Comma-separated metrics gap audit statuses to target, e.g. cdx_cache_missing.")
    parser.add_argument("--audit-pending-only", action="store_true", help="Target only games with fresh pending captures in metrics_backfill_gap_audit.csv.")
    parser.add_argument("--audit-missing-cdx-only", action="store_true", help="Target only games with missing CDX cache files in metrics_backfill_gap_audit.csv.")
    parser.add_argument("--needs-history-only", action="store_true", help="Target only catalog games whose mini-catalog row still needs game-page history.")
    parser.add_argument("--max-fetches", type=int, default=0, help="Limit new metrics JSON fetch attempts this run. 0 means all pending.")
    parser.add_argument("--schemes", default="http,https", help="Comma-separated URL schemes to query, usually http,https.")
    parser.add_argument("--collapse", default="", help="Optional CDX collapse value, e.g. digest. Empty means retain every capture.")
    parser.add_argument("--timeout", type=int, default=18, help="Per-request timeout in seconds.")
    parser.add_argument("--sleep", type=float, default=0.35, help="Seconds to sleep after a metrics JSON fetch.")
    parser.add_argument("--cdx-sleep", type=float, default=0.25, help="Seconds to sleep after a fresh CDX fetch.")
    parser.add_argument("--cdx-retries", type=int, default=1, help="Retries for transient CDX lookup failures.")
    parser.add_argument("--cdx-retry-sleep", type=float, default=1.0, help="Initial seconds to back off between CDX retries.")
    parser.add_argument("--metrics-retries", type=int, default=2, help="Retries for transient archived metrics JSON fetch failures.")
    parser.add_argument("--retry-sleep", type=float, default=1.0, help="Initial seconds to back off between metrics JSON retries.")
    parser.add_argument("--cdx-only", action="store_true", help="Discover and cache CDX rows without fetching archived metrics JSON.")
    parser.add_argument("--refresh-cdx", action="store_true", help="Refresh cached CDX responses.")
    parser.add_argument("--cached-cdx-only", action="store_true", help="Use only existing CDX cache files; skip uncached CDX lookups.")
    parser.add_argument("--retry-failures", action="store_true", help="Retry previously failed metrics JSON captures.")
    args = parser.parse_args()

    for directory in (RAW_CDX, RAW_METRICS_JSON, PROCESSED, LOGS):
        directory.mkdir(parents=True, exist_ok=True)

    schemes = {scheme.strip() for scheme in args.schemes.split(",") if scheme.strip()}
    catalog = load_catalog()
    catalog_scope = catalog[args.catalog_offset :]
    if args.catalog_limit:
        catalog_scope = catalog_scope[: args.catalog_limit]
    audit_statuses = {status.strip() for status in args.audit_statuses.split(",") if status.strip()}
    if audit_statuses or args.audit_pending_only or args.audit_missing_cdx_only:
        audit_rows_by_game = load_audit_rows()

        def audit_row_matches(game: CatalogGame) -> bool:
            audit_row = audit_rows_by_game.get(canonical_game_url(game.game_url), {})
            return (
                (not audit_statuses or audit_row.get("status", "") in audit_statuses)
                and (not args.audit_pending_only or audit_int(audit_row, "fresh_pending_captures") > 0)
                and (not args.audit_missing_cdx_only or audit_int(audit_row, "missing_cdx_cache_files") > 0)
            )

        catalog_scope = [game for game in catalog_scope if audit_row_matches(game)]
    if args.needs_history_only:
        catalog_scope = [game for game in catalog_scope if game.game_name and game.catalog_index >= 0]
        catalog_needs = {
            index: row.get("needs_game_page_history", "")
            for index, row in enumerate(csv.DictReader(CATALOG_CSV.open(newline="", encoding="utf-8")))
        }
        catalog_scope = [game for game in catalog_scope if catalog_needs.get(game.catalog_index) in {"yes", "partial"}]
    manifest = load_manifest()
    failures = load_failures()
    jobs, cdx_stats = build_jobs(
        catalog_scope,
        schemes,
        args.timeout,
        args.cdx_sleep,
        args.refresh_cdx,
        args.max_cdx_games,
        args.collapse,
        args.cdx_retries,
        args.cdx_retry_sleep,
        args.cached_cdx_only,
    )

    pending = [
        job
        for job in jobs
        if not metrics_json_is_valid(metrics_cache_path(job))
        and (args.retry_failures or f"{job.game_url}\t{job.timestamp}\t{job.original}" not in failures)
    ]
    selected = [] if args.cdx_only else pending if args.max_fetches == 0 else pending[: args.max_fetches]

    fetched = 0
    cached = 0
    failed = 0
    for job in selected:
        ok, detail = fetch_metrics(job, args.timeout, args.metrics_retries, args.retry_sleep)
        key = f"{job.game_url}\t{job.timestamp}\t{job.original}"
        if ok:
            if detail == "cached":
                cached += 1
            else:
                fetched += 1
            relative = str(metrics_cache_path(job).relative_to(ROOT))
            manifest[relative] = {
                "game_url": job.game_url,
                "game_name": job.game_name,
                "capture_timestamp": job.timestamp,
                "original_url": job.original,
                "digest": job.digest,
                "mimetype": job.mimetype,
                "length": job.length,
            }
            failures.pop(key, None)
        else:
            failed += 1
            failures[key] = {
                "game_url": job.game_url,
                "game_name": job.game_name,
                "capture_timestamp": job.timestamp,
                "original_url": job.original,
                "last_error": detail,
                "last_attempt_timestamp": utc_now(),
            }
            ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\tjson\t{job.timestamp}\t{job.original}\t{job.game_url}\t{detail}\n")
        if (fetched + cached + failed) % 50 == 0:
            write_json(MANIFEST_PATH, manifest)
            write_json(FAILURE_PATH, failures)
        time.sleep(args.sleep)

    write_json(MANIFEST_PATH, manifest)
    write_json(FAILURE_PATH, failures)

    try:
        from rebuild_game_play_history import rebuild_history as rebuild_combined_history
        from rebuild_game_play_history import write_history as write_combined_history

        history_rows = rebuild_combined_history()
        write_combined_history(history_rows)
    except ImportError:
        history_rows = rebuild_history(manifest)
        write_history(history_rows)

    games_with_history = len({row["game_url"] for row in history_rows})
    report = {
        "run_timestamp": utc_now(),
        "catalog_games": len(catalog),
        "catalog_offset": args.catalog_offset,
        "catalog_limit": args.catalog_limit,
        "audit_statuses": sorted(audit_statuses),
        "audit_pending_only": args.audit_pending_only,
        "audit_missing_cdx_only": args.audit_missing_cdx_only,
        "needs_history_only": args.needs_history_only,
        "catalog_games_in_scope": len(catalog_scope),
        "schemes": sorted(schemes),
        "collapse": args.collapse or "",
        "cached_cdx_only": args.cached_cdx_only,
        **cdx_stats,
        "metrics_jobs": len(jobs),
        "pending_before_run": len(pending),
        "attempted_this_run": len(selected),
        "fetched_this_run": fetched,
        "cached_selected_this_run": cached,
        "failed_this_run": failed,
        "manifest_entries": len(manifest),
        "known_failures": len(failures),
        "history_rows": len(history_rows),
        "games_with_history": games_with_history,
        "first_history_date": history_rows[0]["date"] if history_rows else "",
        "last_history_date": history_rows[-1]["date"] if history_rows else "",
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Kongregate Game Metrics History Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- Catalog games: {report['catalog_games']}",
                f"- Catalog scope: offset {report['catalog_offset']}, limit {report['catalog_limit'] or 'all'} ({report['catalog_games_in_scope']} games)",
                f"- Audit statuses: {', '.join(report['audit_statuses']) or 'all'}",
                f"- Audit pending only: {report['audit_pending_only']}",
                f"- Audit missing CDX only: {report['audit_missing_cdx_only']}",
                f"- Needs history only: {report['needs_history_only']}",
                f"- Schemes: {', '.join(report['schemes'])}",
                f"- Cached CDX only: {report['cached_cdx_only']}",
                f"- CDX games considered: {report['cdx_games_considered']}",
                f"- CDX rows found: {report['cdx_rows']}",
                f"- Missing CDX cache files skipped: {report['cdx_urls_missing_cache_skipped']}",
                f"- Metrics jobs: {report['metrics_jobs']}",
                f"- Pending before run: {report['pending_before_run']}",
                f"- Attempted this run: {report['attempted_this_run']}",
                f"- Fetched this run: {report['fetched_this_run']}",
                f"- Failed this run: {report['failed_this_run']}",
                f"- Manifest entries: {report['manifest_entries']}",
                f"- History rows: {report['history_rows']}",
                f"- Games with history: {report['games_with_history']}",
                f"- History date range: {report['first_history_date']} to {report['last_history_date']}",
                "",
            ]
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
