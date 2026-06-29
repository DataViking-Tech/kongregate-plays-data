#!/usr/bin/env python3
"""Resumable broader scrape for Kongregate ranking pages from Wayback CDX data."""

from __future__ import annotations

import argparse
import gzip
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from pathlib import Path

from extract_ranked_games import infer_source_fields


ROOT = Path(__file__).resolve().parents[1]
RAW_CDX = ROOT / "data" / "raw" / "cdx"
RAW_HTML = ROOT / "data" / "raw" / "html"
LOGS = ROOT / "logs"

CDX_ENDPOINT = "https://web.archive.org/cdx"
WAYBACK_RAW = "https://web.archive.org/web/{timestamp}id_/{original}"
MANIFEST_PATH = RAW_HTML / "manifest.json"
FAILURE_MANIFEST_PATH = RAW_HTML / "failures.json"
REPORT_PATH = LOGS / "full_scrape_report.json"
REPORT_MD_PATH = LOGS / "full_scrape_report.md"
ERROR_LOG = LOGS / "full_scrape_errors.log"

FIELDS = ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]

CDX_SEEDS = {
    "games_sort_gameplays": "https://www.kongregate.com/games?sort=gameplays",
    "games_sort_rating": "https://www.kongregate.com/games?sort=rating",
    "games_sort_newest": "https://www.kongregate.com/games?sort=newest",
    "games_sort_oldest": "https://www.kongregate.com/games?sort=oldest",
    "top_rated_games": "https://www.kongregate.com/top-rated-games",
    "most_played_games": "https://www.kongregate.com/most-played-games",
    "popular_games": "http://www.kongregate.com/popular_games",
    "games": "https://www.kongregate.com/games",
    "action_games": "https://www.kongregate.com/action-games",
    "puzzle_games": "https://www.kongregate.com/puzzle-games",
    "strategy_games": "https://www.kongregate.com/strategy-games",
    "shooter_games": "https://www.kongregate.com/shooter-games",
    "idle_games": "https://www.kongregate.com/idle-games",
    "tower-defense_games": "https://www.kongregate.com/tower-defense-games",
    "en_action_games": "https://www.kongregate.com/en/action-games",
    "en_puzzle_games": "https://www.kongregate.com/en/puzzle-games",
    "en_strategy_games": "https://www.kongregate.com/en/strategy-games",
    "en_shooter_games": "https://www.kongregate.com/en/shooter-games",
    "en_idle_games": "https://www.kongregate.com/en/idle-games",
    "en_tower-defense_games": "https://www.kongregate.com/en/tower-defense-games",
}

SOURCE_PRIORITY = {
    "top_rated_games": 1,
    "games_sort_rating": 2,
    "most_played_games": 3,
    "popular_games": 4,
    "games_sort_gameplays": 5,
    "games_sort_newest": 6,
    "games_sort_oldest": 7,
    "games": 8,
}


@dataclass(frozen=True)
class CaptureJob:
    source_id: str
    timestamp: str
    original: str
    digest: str
    statuscode: str
    mimetype: str
    length: str


def cdx_url(original: str, collapse: str = "digest") -> str:
    params = [
        ("url", original),
        ("output", "json"),
        ("fl", ",".join(FIELDS)),
        ("filter", "statuscode:200"),
        ("filter", "mimetype:text/html"),
        ("collapse", collapse),
    ]
    return f"{CDX_ENDPOINT}?{urllib.parse.urlencode(params)}"


def fetch_cdx(seed_id: str, original: str, sleep_s: float, refresh: bool = False) -> list[dict[str, str]]:
    RAW_CDX.mkdir(parents=True, exist_ok=True)
    cache = RAW_CDX / f"{seed_id}.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text())
    request = urllib.request.Request(cdx_url(original), headers={"User-Agent": "KongregateRankedGamesFullScrape/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read().decode("utf-8", errors="replace")
        data = json.loads(payload)
        headers = data[0] if data else FIELDS
        rows = [dict(zip(headers, row)) for row in data[1:]] if len(data) > 1 else []
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        ERROR_LOG.open("a", encoding="utf-8").write(f"{datetime.utcnow().isoformat()}Z\tcdx\t{seed_id}\t{original}\t{exc}\n")
        rows = []
    cache.write_text(json.dumps(rows, indent=2, sort_keys=True))
    time.sleep(sleep_s)
    return rows


def safe_name(text: str) -> str:
    text = urllib.parse.unquote(text)
    text = text.replace("?sort=", "_sort_")
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", text).strip("_")[:170]


def html_cache_path(timestamp: str, original: str) -> Path:
    digest = sha1(f"{timestamp}:{original}".encode()).hexdigest()[:16]
    return RAW_HTML / f"{timestamp}_{safe_name(original)}_{digest}.html"


def load_manifest() -> dict[str, dict[str, str]]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {}


def save_manifest(manifest: dict[str, dict[str, str]]) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def job_key(job: CaptureJob) -> str:
    return f"{job.timestamp}\t{job.original}"


def load_failures() -> dict[str, dict[str, str]]:
    if FAILURE_MANIFEST_PATH.exists():
        return json.loads(FAILURE_MANIFEST_PATH.read_text())
    failures: dict[str, dict[str, str]] = {}
    if ERROR_LOG.exists():
        for line in ERROR_LOG.read_text(errors="replace").splitlines():
            parts = line.split("\t")
            if len(parts) < 5 or parts[1] != "html":
                continue
            _logged_at, _kind, timestamp, original, detail = parts[:5]
            failures[f"{timestamp}\t{original}"] = {
                "capture_timestamp": timestamp,
                "original_url": original,
                "source_id": "",
                "last_error": detail,
                "last_attempt_timestamp": _logged_at,
            }
    return failures


def save_failures(failures: dict[str, dict[str, str]]) -> None:
    FAILURE_MANIFEST_PATH.write_text(json.dumps(failures, indent=2, sort_keys=True))


def load_jobs(refresh_cdx: bool, sleep_s: float, source_ids: set[str] | None = None) -> list[CaptureJob]:
    jobs: list[CaptureJob] = []
    for seed_id, original in CDX_SEEDS.items():
        if source_ids and seed_id not in source_ids:
            continue
        rows = fetch_cdx(seed_id, original, sleep_s, refresh=refresh_cdx)
        for row in rows:
            ranking_type, _category = infer_source_fields(row.get("original", ""))
            if ranking_type in {"unknown", "homepage_module"}:
                continue
            jobs.append(
                CaptureJob(
                    source_id=seed_id,
                    timestamp=row.get("timestamp", ""),
                    original=row.get("original", ""),
                    digest=row.get("digest", ""),
                    statuscode=row.get("statuscode", ""),
                    mimetype=row.get("mimetype", ""),
                    length=row.get("length", ""),
                )
            )

    deduped: dict[tuple[str, str], CaptureJob] = {}
    for job in jobs:
        if not job.timestamp or not job.original:
            continue
        deduped[(job.timestamp, job.original)] = job

    def priority(job: CaptureJob) -> tuple[int, str, str]:
        source_rank = SOURCE_PRIORITY.get(job.source_id, 20)
        return source_rank, job.timestamp, job.original

    return sorted(deduped.values(), key=priority)


def fetch_html(job: CaptureJob, timeout_s: int) -> tuple[bool, str]:
    target = html_cache_path(job.timestamp, job.original)
    if target.exists() and cached_html_is_valid(target):
        return True, "cached"
    request = urllib.request.Request(
        WAYBACK_RAW.format(timestamp=job.timestamp, original=job.original),
        headers={"User-Agent": "KongregateRankedGamesFullScrape/0.1", "Accept-Encoding": "gzip"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            payload = decode_payload(response.read(), response.headers)
    except urllib.error.HTTPError as exc:
        payload = decode_payload(exc.read(), exc.headers)
        if exc.code >= 500:
            return False, f"http_{exc.code}"
    except (TimeoutError, urllib.error.URLError) as exc:
        return False, str(exc)
    if not payload.strip():
        return False, "empty"
    if not html_text_is_valid(payload):
        return False, "non_html_or_corrupt"
    target.write_text(payload, encoding="utf-8")
    return True, str(target.relative_to(ROOT))


def html_text_is_valid(text: str) -> bool:
    if not text.strip():
        return False
    prefix = text[:4096]
    cleaned = prefix.lstrip("\ufeff\x00\x1f\ufffd\r\n\t ")
    lowered = cleaned[:1200].lower()
    return (
        lowered.startswith("<!doctype")
        or lowered.startswith("<html")
        or lowered.startswith("<turbo-frame")
        or "<html" in lowered
        or "<body" in lowered
    )


def cached_html_is_valid(path: Path) -> bool:
    if not path.exists() or path.stat().st_size <= 0:
        return False
    return html_text_is_valid(path.read_text(errors="replace"))


def decode_payload(payload: bytes, headers) -> str:
    if payload[:2] == b"\x1f\x8b" or str(headers.get("Content-Encoding", "")).lower() == "gzip":
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass
    return payload.decode("utf-8", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Kongregate ranking HTML captures from cached or refreshed CDX data.")
    parser.add_argument("--max-fetches", type=int, default=0, help="Maximum new/cached jobs to process this run. 0 means all remaining jobs.")
    parser.add_argument("--sleep", type=float, default=0.6, help="Seconds to sleep between Wayback HTML requests.")
    parser.add_argument("--cdx-sleep", type=float, default=0.8, help="Seconds to sleep after a new CDX request.")
    parser.add_argument("--timeout", type=int, default=25, help="Per-request timeout in seconds.")
    parser.add_argument("--refresh-cdx", action="store_true", help="Use cached CDX files where present and fetch missing seed files.")
    parser.add_argument("--retry-failures", action="store_true", help="Retry captures that previously failed instead of skipping them.")
    parser.add_argument("--invalid-only", action="store_true", help="Only retry jobs whose HTML cache file exists but is currently invalid.")
    parser.add_argument("--source-id", action="append", default=[], help="Only process one or more source IDs from CDX_SEEDS. May be repeated.")
    parser.add_argument("--from-year", type=int, default=0, help="Only process captures from this year or later.")
    parser.add_argument("--to-year", type=int, default=0, help="Only process captures from this year or earlier.")
    parser.add_argument("--from-timestamp", default="", help="Only process captures at or after this YYYYMMDD or YYYYMMDDhhmmss timestamp.")
    parser.add_argument("--to-timestamp", default="", help="Only process captures at or before this YYYYMMDD or YYYYMMDDhhmmss timestamp.")
    args = parser.parse_args()

    for directory in (RAW_CDX, RAW_HTML, LOGS):
        directory.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest()
    failures = load_failures()
    selected_source_ids = set(args.source_id)
    jobs = load_jobs(refresh_cdx=args.refresh_cdx, sleep_s=args.cdx_sleep, source_ids=selected_source_ids or None)
    if args.source_id:
        jobs = [job for job in jobs if job.source_id in selected_source_ids]
    if args.from_year:
        jobs = [job for job in jobs if job.timestamp[:4].isdigit() and int(job.timestamp[:4]) >= args.from_year]
    if args.to_year:
        jobs = [job for job in jobs if job.timestamp[:4].isdigit() and int(job.timestamp[:4]) <= args.to_year]
    if args.from_timestamp:
        jobs = [job for job in jobs if job.timestamp >= args.from_timestamp.ljust(14, "0")]
    if args.to_timestamp:
        jobs = [job for job in jobs if job.timestamp <= args.to_timestamp.ljust(14, "9")]
    pending = []
    for job in jobs:
        cache_path = html_cache_path(job.timestamp, job.original)
        cache_exists = cache_path.exists()
        cache_valid = cached_html_is_valid(cache_path)
        if cache_valid:
            continue
        if args.invalid_only and not cache_exists:
            continue
        if not args.retry_failures and job_key(job) in failures:
            continue
        pending.append(job)
    selected = pending if args.max_fetches == 0 else pending[: args.max_fetches]

    fetched = 0
    failed = 0
    for job in selected:
        ok, detail = fetch_html(job, args.timeout)
        if ok:
            fetched += 1
            cache_path = html_cache_path(job.timestamp, job.original)
            failures.pop(job_key(job), None)
            manifest[str(cache_path.relative_to(ROOT))] = {
                "capture_timestamp": job.timestamp,
                "original_url": job.original,
                "source_id": job.source_id,
                "digest": job.digest,
                "statuscode": job.statuscode,
                "mimetype": job.mimetype,
                "length": job.length,
            }
            if fetched % 50 == 0:
                save_manifest(manifest)
        else:
            failed += 1
            failures[job_key(job)] = {
                "capture_timestamp": job.timestamp,
                "original_url": job.original,
                "source_id": job.source_id,
                "last_error": detail,
                "last_attempt_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            ERROR_LOG.open("a", encoding="utf-8").write(f"{datetime.utcnow().isoformat()}Z\thtml\t{job.timestamp}\t{job.original}\t{detail}\n")
        time.sleep(args.sleep)

    save_manifest(manifest)
    save_failures(failures)
    remaining_after = len([
        job
        for job in jobs
        if not cached_html_is_valid(html_cache_path(job.timestamp, job.original))
        and job_key(job) not in failures
    ])
    report = {
        "run_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_manifest_jobs": len(jobs),
        "pending_before_run": len(pending),
        "attempted_this_run": len(selected),
        "fetched_or_already_valid_this_run": fetched,
        "failed_this_run": failed,
        "remaining_after_run": remaining_after,
        "manifest_entries": len(manifest),
        "known_failures": len(failures),
        "note": "CDX inputs are digest-collapsed, so duplicate archived HTML content is intentionally not fetched repeatedly.",
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    REPORT_MD_PATH.write_text(
        "\n".join(
            [
                "# Kongregate Full Ranked-Games Scrape Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- Total manifest jobs: {report['total_manifest_jobs']}",
                f"- Pending before run: {report['pending_before_run']}",
                f"- Attempted this run: {report['attempted_this_run']}",
                f"- Fetched this run: {report['fetched_or_already_valid_this_run']}",
                f"- Failed this run: {report['failed_this_run']}",
                f"- Remaining after run: {report['remaining_after_run']}",
                f"- Manifest entries: {report['manifest_entries']}",
                f"- Known failures: {report['known_failures']}",
                "",
                report["note"],
                "",
            ]
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
