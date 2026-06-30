#!/usr/bin/env python3
"""Fetch archived Turbo frame slider HTML discovered in modern Kongregate pages."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from lxml import html as lxml_html

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_ranked_games import infer_original_from_filename, infer_source_fields
from full_ranked_games_scrape import (
    ROOT,
    RAW_HTML,
    LOGS,
    WAYBACK_RAW,
    cached_html_is_valid,
    decode_payload,
    html_cache_path,
    html_text_is_valid,
    load_manifest,
    save_manifest,
)


FRAME_FAILURES_PATH = RAW_HTML / "frame_failures.json"
REPORT_PATH = LOGS / "modern_frame_fetch_report.json"
REPORT_MD_PATH = LOGS / "modern_frame_fetch_report.md"
ERROR_LOG = LOGS / "modern_frame_fetch_errors.log"


@dataclass(frozen=True)
class FrameJob:
    parent_path: Path
    parent_timestamp: str
    parent_original: str
    frame_src: str
    frame_original: str


def load_json(path: Path) -> dict[str, dict[str, str]]:
    return json.loads(path.read_text()) if path.exists() else {}


def save_json(path: Path, payload: dict[str, dict[str, str]]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def frame_key(job: FrameJob) -> str:
    return f"{job.parent_timestamp}\t{job.frame_original}"


def final_wayback_timestamp(url: str, fallback: str) -> str:
    match = re.search(r"/web/(\d{14})(?:[a-z_]+)?/", url)
    return match.group(1) if match else fallback


def read_sample_meta(path: Path, manifest: dict[str, dict[str, str]]) -> tuple[str, str, str]:
    doc = path.read_text(errors="replace")
    manifest_row = manifest.get(str(path.relative_to(ROOT)), {})
    timestamp = manifest_row.get("capture_timestamp", "")
    original = manifest_row.get("original_url", "")
    if not timestamp or not original:
        timestamp, original = infer_original_from_filename(path, doc)
    return timestamp, original, doc


def discover_frame_jobs(from_year: int) -> list[FrameJob]:
    manifest = load_manifest()
    jobs: dict[tuple[str, str], FrameJob] = {}
    for path in sorted(RAW_HTML.glob("*.html")):
        try:
            timestamp, original, doc_text = read_sample_meta(path, manifest)
            if not timestamp or int(timestamp[:4]) < from_year:
                continue
            ranking_type, _category = infer_source_fields(original)
            if ranking_type in {"unknown", "homepage_module"}:
                continue
            doc = lxml_html.fromstring(doc_text)
        except Exception:
            continue
        for frame_src in doc.xpath("//turbo-frame[contains(@src, '/slider')]/@src"):
            frame_original = urllib.parse.urljoin(original, frame_src)
            key = (timestamp, frame_original)
            jobs[key] = FrameJob(
                parent_path=path,
                parent_timestamp=timestamp,
                parent_original=original,
                frame_src=frame_src,
                frame_original=frame_original,
            )
    return sorted(jobs.values(), key=lambda job: (job.parent_timestamp, job.frame_original))


def fetch_frame(job: FrameJob, timeout_s: int) -> tuple[bool, str, str]:
    target = html_cache_path(job.parent_timestamp, job.frame_original)
    if target.exists() and cached_html_is_valid(target):
        return True, "cached", job.parent_timestamp
    request = urllib.request.Request(
        WAYBACK_RAW.format(timestamp=job.parent_timestamp, original=job.frame_original),
        headers={"User-Agent": "KongregateModernFrameFetch/0.1", "Accept-Encoding": "gzip"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            payload = decode_payload(response.read(), response.headers)
            actual_timestamp = final_wayback_timestamp(response.url, job.parent_timestamp)
    except urllib.error.HTTPError as exc:
        payload = decode_payload(exc.read(), exc.headers)
        actual_timestamp = final_wayback_timestamp(exc.url, job.parent_timestamp)
        if exc.code >= 500:
            return False, f"http_{exc.code}", actual_timestamp
    except (TimeoutError, urllib.error.URLError) as exc:
        return False, str(exc), job.parent_timestamp
    if not payload.strip():
        return False, "empty", actual_timestamp
    if not html_text_is_valid(payload):
        return False, "non_html_or_corrupt", actual_timestamp
    target.write_text(payload, encoding="utf-8")
    return True, str(target.relative_to(ROOT)), actual_timestamp


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch modern Kongregate Turbo slider frames from Wayback.")
    parser.add_argument("--max-fetches", type=int, default=0, help="Maximum new frame fetches. 0 means all pending frames.")
    parser.add_argument("--from-year", type=int, default=2023, help="Only inspect parent captures from this year onward.")
    parser.add_argument("--from-timestamp", default="", help="Only process parent captures at or after this YYYYMMDD or YYYYMMDDhhmmss timestamp.")
    parser.add_argument("--to-timestamp", default="", help="Only process parent captures at or before this YYYYMMDD or YYYYMMDDhhmmss timestamp.")
    parser.add_argument("--sleep", type=float, default=0.6, help="Seconds to sleep between Wayback frame requests.")
    parser.add_argument("--timeout", type=int, default=30, help="Per-request timeout in seconds.")
    parser.add_argument("--retry-failures", action="store_true", help="Retry frames that previously failed.")
    args = parser.parse_args()

    for directory in (RAW_HTML, LOGS):
        directory.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest()
    failures = load_json(FRAME_FAILURES_PATH)
    jobs = discover_frame_jobs(args.from_year)
    if args.from_timestamp:
        jobs = [job for job in jobs if job.parent_timestamp >= args.from_timestamp.ljust(14, "0")]
    if args.to_timestamp:
        jobs = [job for job in jobs if job.parent_timestamp <= args.to_timestamp.ljust(14, "9")]
    for job in jobs:
        if cached_html_is_valid(html_cache_path(job.parent_timestamp, job.frame_original)):
            failures.pop(frame_key(job), None)
    pending = [
        job
        for job in jobs
        if not cached_html_is_valid(html_cache_path(job.parent_timestamp, job.frame_original))
        and (args.retry_failures or frame_key(job) not in failures)
    ]
    selected = pending if args.max_fetches == 0 else pending[: args.max_fetches]

    fetched = 0
    failed = 0
    for job in selected:
        ok, detail, actual_timestamp = fetch_frame(job, args.timeout)
        if ok:
            fetched += 1
            cache_path = html_cache_path(job.parent_timestamp, job.frame_original)
            failures.pop(frame_key(job), None)
            manifest[str(cache_path.relative_to(ROOT))] = {
                "capture_timestamp": actual_timestamp,
                "original_url": job.frame_original,
                "source_id": "turbo_frame_slider",
                "parent_html_path": str(job.parent_path.relative_to(ROOT)),
                "parent_capture_timestamp": job.parent_timestamp,
                "parent_original_url": job.parent_original,
                "frame_src": job.frame_src,
                "statuscode": "200",
                "mimetype": "text/html",
                "length": str(cache_path.stat().st_size),
            }
            if fetched % 25 == 0:
                save_manifest(manifest)
        else:
            failed += 1
            failures[frame_key(job)] = {
                "capture_timestamp": job.parent_timestamp,
                "original_url": job.frame_original,
                "source_id": "turbo_frame_slider",
                "parent_html_path": str(job.parent_path.relative_to(ROOT)),
                "last_error": detail,
                "last_attempt_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            ERROR_LOG.open("a", encoding="utf-8").write(f"{datetime.utcnow().isoformat()}Z\tframe\t{job.parent_timestamp}\t{job.frame_original}\t{detail}\n")
        time.sleep(args.sleep)

    save_manifest(manifest)
    save_json(FRAME_FAILURES_PATH, failures)
    remaining_after = len([
        job
        for job in jobs
        if not cached_html_is_valid(html_cache_path(job.parent_timestamp, job.frame_original))
        and frame_key(job) not in failures
    ])
    report = {
        "run_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frame_jobs_discovered": len(jobs),
        "pending_before_run": len(pending),
        "attempted_this_run": len(selected),
        "fetched_this_run": fetched,
        "failed_this_run": failed,
        "remaining_after_run": remaining_after,
        "manifest_entries": len(manifest),
        "known_frame_failures": len(failures),
        "note": "Frame rows use the actual Wayback timestamp when replay resolves to a nearby frame capture.",
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    REPORT_MD_PATH.write_text(
        "\n".join(
            [
                "# Kongregate Modern Frame Fetch Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- Frame jobs discovered: {report['frame_jobs_discovered']}",
                f"- Pending before run: {report['pending_before_run']}",
                f"- Attempted this run: {report['attempted_this_run']}",
                f"- Fetched this run: {report['fetched_this_run']}",
                f"- Failed this run: {report['failed_this_run']}",
                f"- Remaining after run: {report['remaining_after_run']}",
                f"- Manifest entries: {report['manifest_entries']}",
                f"- Known frame failures: {report['known_frame_failures']}",
                "",
                report["note"],
                "",
            ]
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
