#!/usr/bin/env python3
"""Fetch current Kongregate ranking/listing pages into the ranked-page cache."""

from __future__ import annotations

import argparse
import gzip
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path

from extract_ranked_games import infer_source_fields
from full_ranked_games_scrape import ROOT, RAW_HTML, cached_html_is_valid, html_text_is_valid, load_manifest, save_manifest


LOGS = ROOT / "logs"
REPORT_JSON = LOGS / "live_ranked_pages_report.json"
REPORT_MD = LOGS / "live_ranked_pages_report.md"
ERROR_LOG = LOGS / "live_ranked_pages_errors.log"

DEFAULT_SOURCES = {
    "live_en_action_games": "https://www.kongregate.com/en/action-games",
    "live_en_adventure_games": "https://www.kongregate.com/en/adventure-games",
    "live_en_puzzle_games": "https://www.kongregate.com/en/puzzle-games",
    "live_en_strategy_games": "https://www.kongregate.com/en/strategy-games",
    "live_en_shooter_games": "https://www.kongregate.com/en/shooter-games",
    "live_en_idle_games": "https://www.kongregate.com/en/idle-games",
    "live_en_tower-defense_games": "https://www.kongregate.com/en/tower-defense-games",
    "live_en_multiplayer_games": "https://www.kongregate.com/en/multiplayer-games",
    "live_en_mmo_games": "https://www.kongregate.com/en/mmo-games",
    "live_en_adventure-rpg_games": "https://www.kongregate.com/en/adventure-rpg-games",
    "live_en_sports-racing_games": "https://www.kongregate.com/en/sports-racing-games",
    "live_en_strategy-defense_games": "https://www.kongregate.com/en/strategy-defense-games",
    "live_en_more_games": "https://www.kongregate.com/en/more-games",
    "live_en_card_games": "https://www.kongregate.com/en/card-games",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def timestamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def safe_name(text: str) -> str:
    text = urllib.parse.unquote(text)
    text = text.replace("?sort=", "_sort_")
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", text).strip("_")[:170]


def html_cache_path(timestamp: str, original: str) -> Path:
    digest = sha1(f"{timestamp}:{original}".encode()).hexdigest()[:16]
    return RAW_HTML / f"{timestamp}_{safe_name(original)}_{digest}.html"


def decode_payload(payload: bytes, headers) -> str:
    if payload[:2] == b"\x1f\x8b" or str(headers.get("Content-Encoding", "")).lower() == "gzip":
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass
    return payload.decode("utf-8", errors="replace")


def fetch_live_page(url: str, timeout_s: int) -> tuple[bool, str, str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "KongregateCurrentRankedFetch/0.1",
            "Accept": "text/html,*/*",
            "Accept-Encoding": "gzip",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            payload = decode_payload(response.read(), response.headers)
            final_url = response.url
    except urllib.error.HTTPError as exc:
        return False, f"http_{exc.code}", exc.url, ""
    except (TimeoutError, urllib.error.URLError) as exc:
        return False, str(exc), url, ""
    if not payload.strip():
        return False, "empty", final_url, ""
    if not html_text_is_valid(payload):
        return False, "non_html_or_corrupt", final_url, ""
    return True, "fetched", final_url, payload


def final_url_matches_source(requested_url: str, final_url: str) -> bool:
    requested_type, requested_category = infer_source_fields(requested_url)
    final_type, final_category = infer_source_fields(final_url)
    return requested_type == final_type and requested_category == final_category


def parse_sources(source_args: list[str]) -> dict[str, str]:
    if not source_args:
        return dict(DEFAULT_SOURCES)
    sources = {}
    for item in source_args:
        if "=" not in item:
            raise SystemExit(f"--source must be source_id=url, got: {item}")
        source_id, url = item.split("=", 1)
        source_id = source_id.strip()
        url = url.strip()
        if not source_id or not url:
            raise SystemExit(f"--source must be source_id=url, got: {item}")
        sources[source_id] = url
    return sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch current live Kongregate ranked/listing pages.")
    parser.add_argument("--source", action="append", default=[], help="Fetch only source_id=url. May be repeated.")
    parser.add_argument("--max-fetches", type=int, default=0, help="Limit source pages fetched. 0 means all selected sources.")
    parser.add_argument("--timeout", type=int, default=20, help="Per-page request timeout in seconds.")
    parser.add_argument("--sleep", type=float, default=0.25, help="Seconds to sleep between live page requests.")
    parser.add_argument("--timestamp", default="", help="Override capture timestamp, YYYYMMDDhhmmss. Defaults to now.")
    args = parser.parse_args()

    RAW_HTML.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    sources = parse_sources(args.source)
    timestamp = args.timestamp or timestamp_now()
    selected = list(sources.items())
    if args.max_fetches:
        selected = selected[: args.max_fetches]

    manifest = load_manifest()
    fetched = 0
    failed = 0
    skipped_unknown = 0
    rows = []
    for source_id, url in selected:
        ranking_type, category = infer_source_fields(url)
        if ranking_type == "unknown":
            skipped_unknown += 1
            rows.append({"source_id": source_id, "url": url, "status": "skipped_unknown_source"})
            continue
        ok, detail, final_url, payload = fetch_live_page(url, args.timeout)
        target = html_cache_path(timestamp, url)
        if ok and not final_url_matches_source(url, final_url):
            ok = False
            detail = "redirected_to_different_source"
        if ok:
            target.write_text(payload, encoding="utf-8")
            fetched += 1
            manifest[str(target.relative_to(ROOT))] = {
                "capture_timestamp": timestamp,
                "original_url": url,
                "capture_url": final_url,
                "source_id": source_id,
                "source_kind": "live_current",
                "ranking_type": ranking_type,
                "category": category,
                "statuscode": "200",
                "mimetype": "text/html",
                "length": str(target.stat().st_size),
            }
            status = "fetched"
        else:
            failed += 1
            ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\tlive_html\t{source_id}\t{url}\t{detail}\n")
            status = detail
        rows.append({"source_id": source_id, "url": url, "final_url": final_url, "status": status})
        time.sleep(args.sleep)

    save_manifest(manifest)
    valid_after = sum(1 for _source_id, url in selected if cached_html_is_valid(html_cache_path(timestamp, url)))
    report = {
        "run_timestamp": utc_now(),
        "capture_timestamp": timestamp,
        "sources_selected": len(selected),
        "fetched_this_run": fetched,
        "failed_this_run": failed,
        "skipped_unknown_source": skipped_unknown,
        "valid_cached_for_timestamp": valid_after,
        "manifest_entries": len(manifest),
        "sources": rows,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2))
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Kongregate Live Ranked Pages Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- Capture timestamp: {report['capture_timestamp']}",
                f"- Sources selected: {report['sources_selected']}",
                f"- Fetched this run: {report['fetched_this_run']}",
                f"- Failed this run: {report['failed_this_run']}",
                f"- Skipped unknown source: {report['skipped_unknown_source']}",
                f"- Valid cached for timestamp: {report['valid_cached_for_timestamp']}",
                f"- Manifest entries: {report['manifest_entries']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
