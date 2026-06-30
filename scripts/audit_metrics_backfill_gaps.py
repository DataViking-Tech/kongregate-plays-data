#!/usr/bin/env python3
"""Classify remaining per-game metrics backfill gaps for the mini catalog."""

from __future__ import annotations

import csv
import json
import re
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from fetch_game_metrics_history import (
    MetricsJob,
    cdx_cache_path,
    load_failures,
    metric_cdx_keys_for_game,
    metrics_cache_path,
    metrics_json_is_valid,
)


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

CATALOG_CSV = PROCESSED / "mini_catalog.csv"
PRIORITIES_CSV = PROCESSED / "catalog_history_priorities.csv"
HISTORY_CSV = PROCESSED / "game_play_history.csv"
AUDIT_CSV = PROCESSED / "metrics_backfill_gap_audit.csv"
REPORT_JSON = LOGS / "metrics_backfill_gap_audit_report.json"
REPORT_MD = LOGS / "metrics_backfill_gap_audit_report.md"

AUDIT_COLUMNS = [
    "catalog_index",
    "game_name",
    "game_url",
    "canonical_game_key",
    "status",
    "priority_score",
    "best_rank",
    "top_n_appearances",
    "listing_play_count_rows",
    "needs_game_page_history",
    "metrics_rows",
    "first_metric_date",
    "last_metric_date",
    "cdx_rows",
    "valid_cached_captures",
    "known_failed_captures",
    "fresh_pending_captures",
    "missing_cdx_cache_files",
    "failure_errors",
    "first_seen_date",
    "last_seen_date",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_int(value: object) -> int:
    text = str(value or "").replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def canonical_game_url(game_url: str) -> str:
    if not game_url:
        return ""
    parsed = urllib.parse.urlsplit(game_url)
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/]+)", parsed.path)
    if not match:
        return game_url.lower()
    developer, slug = match.groups()
    return f"www.kongregate.com/games/{urllib.parse.unquote(developer)}/{urllib.parse.unquote(slug)}".lower()


def load_history_stats() -> dict[str, dict[str, object]]:
    stats: dict[str, dict[str, object]] = defaultdict(lambda: {"rows": 0, "dates": []})
    for row in read_csv(HISTORY_CSV):
        key = canonical_game_url(row.get("game_url", ""))
        if not key:
            continue
        stats[key]["rows"] += 1
        if row.get("date"):
            stats[key]["dates"].append(row["date"])

    for game_stats in stats.values():
        dates = sorted(game_stats["dates"])
        game_stats["first_metric_date"] = dates[0] if dates else ""
        game_stats["last_metric_date"] = dates[-1] if dates else ""
    return stats


def load_priority_rows() -> dict[str, dict[str, str]]:
    rows = {}
    for row in read_csv(PRIORITIES_CSV):
        key = canonical_game_url(row.get("game_url", ""))
        if key:
            rows[key] = row
    return rows


def game_url_variants(row: dict[str, str]) -> tuple[str, ...]:
    variants = []
    if row.get("game_url"):
        variants.append(row["game_url"])
    variants.extend(part.strip() for part in row.get("game_url_variants", "").split(";") if part.strip())
    return tuple(dict.fromkeys(variants))


def failure_indexes() -> tuple[set[tuple[str, str, str]], dict[str, Counter]]:
    signatures = set()
    errors_by_game: dict[str, Counter] = defaultdict(Counter)
    for failure in load_failures().values():
        key = canonical_game_url(failure.get("game_url", ""))
        timestamp = failure.get("capture_timestamp", "")
        original = failure.get("original_url", "")
        if key and timestamp and original:
            signatures.add((key, timestamp, original))
            errors_by_game[key][failure.get("last_error", "unknown_error")] += 1
    return signatures, errors_by_game


def cached_cdx_rows(catalog_index: int, game_url: str, game_name: str, variants: tuple[str, ...]) -> tuple[list[MetricsJob], int]:
    jobs = {}
    missing_cache_files = 0
    metrics_urls = []
    for variant in variants or (game_url,):
        metrics_urls.extend(metric_cdx_keys_for_game(variant))
    for metrics_url in dict.fromkeys(metrics_urls):
        cache_path = cdx_cache_path(metrics_url)
        if not cache_path.exists():
            missing_cache_files += 1
            continue
        try:
            cdx_rows = json.loads(cache_path.read_text())
        except json.JSONDecodeError:
            missing_cache_files += 1
            continue
        for row in cdx_rows:
            timestamp = row.get("timestamp", "")
            original = row.get("original", metrics_url)
            if not timestamp or not original:
                continue
            job = MetricsJob(
                catalog_index=catalog_index,
                game_url=game_url,
                game_name=game_name,
                timestamp=timestamp,
                original=original,
                digest=row.get("digest", ""),
                mimetype=row.get("mimetype", ""),
                length=row.get("length", ""),
            )
            jobs[(timestamp, original)] = job
    return sorted(jobs.values(), key=lambda job: (job.timestamp, job.original)), missing_cache_files


def classify_row(
    metrics_rows: int,
    valid_cached_captures: int,
    fresh_pending_captures: int,
    known_failed_captures: int,
    cdx_rows: int,
    missing_cdx_cache_files: int,
) -> str:
    if metrics_rows:
        return "has_metrics"
    if valid_cached_captures:
        return "cached_not_in_history"
    if fresh_pending_captures:
        return "fresh_pending"
    if known_failed_captures:
        return "known_failures_only"
    if missing_cdx_cache_files:
        return "cdx_cache_missing"
    if cdx_rows == 0:
        return "no_cdx"
    return "unknown"


def summarize_errors(counter: Counter) -> str:
    return "; ".join(f"{error} ({count})" for error, count in counter.most_common(3))


def main() -> None:
    catalog_rows = read_csv(CATALOG_CSV)
    priority_rows = load_priority_rows()
    history_stats = load_history_stats()
    failure_signatures, errors_by_game = failure_indexes()

    audit_rows = []
    for catalog_index, catalog_row in enumerate(catalog_rows):
        game_url = catalog_row.get("game_url", "")
        game_name = catalog_row.get("game_name", "")
        key = catalog_row.get("canonical_game_key") or canonical_game_url(game_url)
        priority = priority_rows.get(key, {})
        history = history_stats.get(key, {})

        cdx_jobs, missing_cdx_cache_files = cached_cdx_rows(catalog_index, game_url, game_name, game_url_variants(catalog_row))
        valid_cached_captures = 0
        known_failed_captures = 0
        fresh_pending_captures = 0

        for job in cdx_jobs:
            if metrics_json_is_valid(metrics_cache_path(job)):
                valid_cached_captures += 1
            elif (key, job.timestamp, job.original) in failure_signatures:
                known_failed_captures += 1
            else:
                fresh_pending_captures += 1

        metrics_rows = parse_int(history.get("rows", 0))
        status = classify_row(
            metrics_rows=metrics_rows,
            valid_cached_captures=valid_cached_captures,
            fresh_pending_captures=fresh_pending_captures,
            known_failed_captures=known_failed_captures,
            cdx_rows=len(cdx_jobs),
            missing_cdx_cache_files=missing_cdx_cache_files,
        )

        audit_rows.append(
            {
                "catalog_index": catalog_index,
                "game_name": game_name,
                "game_url": game_url,
                "canonical_game_key": key,
                "status": status,
                "priority_score": parse_int(priority.get("priority_score")),
                "best_rank": catalog_row.get("best_rank", ""),
                "top_n_appearances": catalog_row.get("top_n_appearances", ""),
                "listing_play_count_rows": catalog_row.get("listing_play_count_rows", ""),
                "needs_game_page_history": catalog_row.get("needs_game_page_history", ""),
                "metrics_rows": metrics_rows,
                "first_metric_date": history.get("first_metric_date", ""),
                "last_metric_date": history.get("last_metric_date", ""),
                "cdx_rows": len(cdx_jobs),
                "valid_cached_captures": valid_cached_captures,
                "known_failed_captures": known_failed_captures,
                "fresh_pending_captures": fresh_pending_captures,
                "missing_cdx_cache_files": missing_cdx_cache_files,
                "failure_errors": summarize_errors(errors_by_game.get(key, Counter())),
                "first_seen_date": catalog_row.get("first_seen_date", ""),
                "last_seen_date": catalog_row.get("last_seen_date", ""),
            }
        )

    audit_rows.sort(
        key=lambda row: (
            row["status"] == "has_metrics",
            row["status"] == "cached_not_in_history",
            -parse_int(row["fresh_pending_captures"]),
            -parse_int(row["priority_score"]),
            parse_int(row["best_rank"]) or 9999,
            str(row["game_name"]).lower(),
        )
    )

    write_csv(AUDIT_CSV, AUDIT_COLUMNS, audit_rows)

    status_counts = Counter(row["status"] for row in audit_rows)
    unresolved_rows = [row for row in audit_rows if row["status"] != "has_metrics"]
    fresh_pending_rows = [row for row in audit_rows if parse_int(row["fresh_pending_captures"]) > 0]
    no_metrics_rows = [row for row in audit_rows if parse_int(row["metrics_rows"]) == 0]
    report = {
        "generated_at": utc_now(),
        "catalog_games": len(audit_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "games_without_metrics_rows": len(no_metrics_rows),
        "games_with_fresh_pending_captures": len(fresh_pending_rows),
        "fresh_pending_captures": sum(parse_int(row["fresh_pending_captures"]) for row in audit_rows),
        "known_failed_captures": sum(parse_int(row["known_failed_captures"]) for row in audit_rows),
        "valid_cached_captures": sum(parse_int(row["valid_cached_captures"]) for row in audit_rows),
        "missing_cdx_cache_files": sum(parse_int(row["missing_cdx_cache_files"]) for row in audit_rows),
        "top_unresolved_games": [
            {
                "game_name": row["game_name"],
                "status": row["status"],
                "priority_score": row["priority_score"],
                "best_rank": row["best_rank"],
                "metrics_rows": row["metrics_rows"],
                "cdx_rows": row["cdx_rows"],
                "fresh_pending_captures": row["fresh_pending_captures"],
                "known_failed_captures": row["known_failed_captures"],
                "failure_errors": row["failure_errors"],
            }
            for row in unresolved_rows[:25]
        ],
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True))

    lines = [
        "# Metrics Backfill Gap Audit",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Mini-catalog games audited: {report['catalog_games']}",
        f"- Games without metrics rows: {report['games_without_metrics_rows']}",
        f"- Games with fresh pending captures: {report['games_with_fresh_pending_captures']}",
        f"- Fresh pending captures: {report['fresh_pending_captures']}",
        f"- Known failed captures: {report['known_failed_captures']}",
        f"- Missing CDX cache files: {report['missing_cdx_cache_files']}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in report["status_counts"].items():
        lines.append(f"- {status}: {count}")

    lines.extend(["", "## Top Unresolved Games", ""])
    if report["top_unresolved_games"]:
        lines.append("| Game | Status | Best rank | Metrics rows | CDX rows | Fresh pending | Known failed |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
        for row in report["top_unresolved_games"]:
            lines.append(
                "| {game_name} | {status} | {best_rank} | {metrics_rows} | {cdx_rows} | {fresh_pending_captures} | {known_failed_captures} |".format(
                    **row
                )
            )
    else:
        lines.append("No unresolved games remain.")

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- `{AUDIT_CSV.relative_to(ROOT)}`",
            f"- `{REPORT_JSON.relative_to(ROOT)}`",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
