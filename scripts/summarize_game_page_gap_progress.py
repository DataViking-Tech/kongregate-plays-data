#!/usr/bin/env python3
"""Summarize cumulative game-page backfill progress for no-CDX gaps."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from fetch_game_page_history import FAILURE_PATH, MANIFEST_PATH, PROFILE_CSV, ROOT, cdx_cache_paths_for_url, load_profile_games, parse_int
from kongregate_canonical import canonical_game_url


PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"
OUTPUT_CSV = PROCESSED / "game_page_gap_progress.csv"
PROBE_HISTORY_CSV = PROCESSED / "count_source_probe_history.csv"
REPORT_JSON = LOGS / "game_page_gap_progress_report.json"
REPORT_MD = LOGS / "game_page_gap_progress_report.md"

OUTPUT_COLUMNS = [
    "status",
    "followup_tier",
    "game_name",
    "game_url",
    "canonical_game_key",
    "best_rank",
    "top_n_appearances",
    "listing_play_count_rows",
    "needs_game_page_history",
    "first_seen_date",
    "last_seen_date",
    "cached_cdx_variants",
    "unique_cdx_rows",
    "parsed_page_rows",
    "failed_page_rows",
    "no_explicit_count_failures",
    "network_or_fetch_failures",
    "dynamic_metric_placeholder_pages",
    "game_metrics_updater_pages",
    "blank_gameplays_count_pages",
    "metrics_json_probe_observations",
    "metrics_json_cdx_rows",
    "alternate_endpoint_cdx_rows",
    "recommended_next_action",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_tiers(value: str) -> set[int]:
    return {parse_int(part) for part in value.split(",") if part.strip()}


def cdx_rows_for_game(game) -> tuple[int, int]:
    cached_variants = 0
    unique_rows = set()
    for page_url in game.game_url_variants:
        paths = [path for path in cdx_cache_paths_for_url(page_url) if path.exists()]
        if not paths:
            continue
        cached_variants += 1
        for path in paths:
            try:
                rows = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            for row in rows:
                unique_rows.add((row.get("timestamp", ""), row.get("original", ""), row.get("digest", "")))
    return cached_variants, len(unique_rows)


def read_probe_history() -> dict[str, list[dict[str, str]]]:
    rows_by_key: dict[str, list[dict[str, str]]] = {}
    if not PROBE_HISTORY_CSV.exists():
        return rows_by_key
    with PROBE_HISTORY_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = canonical_game_url(row.get("game_url", ""))
            if key:
                rows_by_key.setdefault(key, []).append(row)
    return rows_by_key


def cached_page_evidence(failures: list[dict[str, object]]) -> dict[str, int]:
    evidence = {
        "dynamic_metric_placeholder_pages": 0,
        "game_metrics_updater_pages": 0,
        "blank_gameplays_count_pages": 0,
    }
    for failure in failures:
        if failure.get("last_error") != "no_explicit_count":
            continue
        relative_path = str(failure.get("cached_html", "") or "")
        if not relative_path:
            continue
        path = ROOT / relative_path
        if not path.exists() or path.stat().st_size <= 0:
            continue
        markup = path.read_text(errors="replace")
        has_updater = "GameMetricsUpdater.update" in markup
        has_blank_gameplays = bool(
            re.search(
                r"class=[\"'][^\"']*\bgameplays_count\b[^\"']*[\"'][^>]*>\s*</",
                markup,
                flags=re.IGNORECASE,
            )
        )
        evidence["game_metrics_updater_pages"] += int(has_updater)
        evidence["blank_gameplays_count_pages"] += int(has_blank_gameplays)
        evidence["dynamic_metric_placeholder_pages"] += int(has_updater and has_blank_gameplays)
    return evidence


def probe_evidence(rows: list[dict[str, str]]) -> dict[str, int]:
    metrics_rows = [row for row in rows if row.get("source_type") == "metrics_json"]
    alternate_rows = [row for row in rows if row.get("source_type") != "metrics_json"]
    return {
        "metrics_json_probe_observations": len(metrics_rows),
        "metrics_json_cdx_rows": sum(parse_int(row.get("cdx_rows")) for row in metrics_rows),
        "alternate_endpoint_cdx_rows": sum(parse_int(row.get("cdx_rows")) for row in alternate_rows),
    }


def status_and_action(
    cached_cdx_variants: int,
    cdx_rows: int,
    parsed_rows: int,
    failures: list[dict[str, object]],
    page_evidence: dict[str, int],
    endpoint_evidence: dict[str, int],
) -> tuple[str, str]:
    no_explicit = sum(1 for failure in failures if failure.get("last_error") == "no_explicit_count")
    network_or_fetch = len(failures) - no_explicit
    if parsed_rows:
        return "parsed_page_count", "No immediate action; page HTML has yielded at least one play-count observation."
    if no_explicit and cdx_rows:
        if page_evidence["dynamic_metric_placeholder_pages"]:
            if endpoint_evidence["metrics_json_probe_observations"] and endpoint_evidence["metrics_json_cdx_rows"] == 0:
                return (
                    "dynamic_metrics_placeholder",
                    "Escalate to alternate list/external sources; archived HTML defers counts to metrics.json and exact metrics endpoints have no CDX rows.",
                )
            return (
                "dynamic_metrics_placeholder",
                "Probe exact archived metrics.json endpoints; cached HTML defers counts to JavaScript-injected metrics.",
            )
        return "html_without_explicit_count", "Probe adjacent archived JSON/API routes; cached HTML appears to rely on JavaScript-injected metrics."
    if network_or_fetch and cdx_rows:
        return "page_fetch_failed", "Retry archived page fetches with a small shard and retry-failures enabled."
    if cdx_rows:
        return "page_cdx_pending", "Fetch and parse the discovered archived game-page captures."
    if cached_cdx_variants:
        return "no_page_cdx_rows", "Escalate to alternate count sources; checked page URL variants have no usable CDX rows."
    return "not_checked", "Run a bounded page-history CDX shard for this game."


def progress_rows(args) -> list[dict[str, object]]:
    games = load_profile_games(Path(args.input_csv), parse_tiers(args.tiers))
    if args.metrics_row_status == "no_metrics":
        games = [game for game in games if game.metrics_rows == 0]
    elif args.metrics_row_status == "has_metrics":
        games = [game for game in games if game.metrics_rows > 0]

    manifest = read_json(MANIFEST_PATH, {})
    failures = read_json(FAILURE_PATH, {})
    parsed_by_game = Counter(str(meta.get("canonical_game_key", "")) for meta in manifest.values())
    failures_by_game: dict[str, list[dict[str, object]]] = {}
    for meta in failures.values():
        key = str(meta.get("canonical_game_key", ""))
        if key:
            failures_by_game.setdefault(key, []).append(meta)
    probe_rows_by_game = read_probe_history()

    rows: list[dict[str, object]] = []
    for game in games:
        cached_variants, unique_cdx_rows = cdx_rows_for_game(game)
        game_failures = failures_by_game.get(game.canonical_key, [])
        parsed_rows = parsed_by_game.get(game.canonical_key, 0)
        page_evidence = cached_page_evidence(game_failures)
        endpoint_evidence = probe_evidence(probe_rows_by_game.get(game.canonical_key, []))
        status, action = status_and_action(
            cached_variants,
            unique_cdx_rows,
            parsed_rows,
            game_failures,
            page_evidence,
            endpoint_evidence,
        )
        no_explicit = sum(1 for failure in game_failures if failure.get("last_error") == "no_explicit_count")
        rows.append(
            {
                "status": status,
                "followup_tier": game.tier,
                "game_name": game.game_name,
                "game_url": game.game_url,
                "canonical_game_key": game.canonical_key,
                "best_rank": game.best_rank,
                "top_n_appearances": game.top_n_appearances,
                "listing_play_count_rows": game.listing_play_count_rows,
                "needs_game_page_history": "yes" if game.tier == 1 else "",
                "first_seen_date": game.first_seen_date,
                "last_seen_date": game.last_seen_date,
                "cached_cdx_variants": cached_variants,
                "unique_cdx_rows": unique_cdx_rows,
                "parsed_page_rows": parsed_rows,
                "failed_page_rows": len(game_failures),
                "no_explicit_count_failures": no_explicit,
                "network_or_fetch_failures": len(game_failures) - no_explicit,
                **page_evidence,
                **endpoint_evidence,
                "recommended_next_action": action,
            }
        )
    rows.sort(
        key=lambda row: (
            int(row["followup_tier"]),
            int(row["best_rank"] or 999999),
            row["status"],
            str(row["first_seen_date"]),
            str(row["game_name"]).lower(),
        )
    )
    return rows


def write_report(rows: list[dict[str, object]], args) -> dict[str, object]:
    status_counts = Counter(str(row["status"]) for row in rows)
    action_counts = Counter(str(row["recommended_next_action"]) for row in rows)
    high_value_unresolved = [
        row
        for row in rows
        if int(row["followup_tier"]) == 1 and row["status"] != "parsed_page_count"
    ]
    examples = high_value_unresolved[:30]
    dynamic_rows = [row for row in rows if parse_int(row.get("dynamic_metric_placeholder_pages")) > 0]
    metrics_checked_rows = [row for row in dynamic_rows if parse_int(row.get("metrics_json_probe_observations")) > 0]
    report = {
        "generated_at": utc_now(),
        "input_csv": args.input_csv,
        "tiers": sorted(parse_tiers(args.tiers)),
        "metrics_row_status": args.metrics_row_status,
        "profile_games": len(rows),
        "status_counts": dict(status_counts.most_common()),
        "recommended_action_counts": dict(action_counts.most_common()),
        "dynamic_metric_placeholder_games": len(dynamic_rows),
        "dynamic_metric_placeholder_games_with_metrics_json_probe": len(metrics_checked_rows),
        "dynamic_metric_placeholder_games_with_metrics_json_cdx_rows": sum(
            1 for row in dynamic_rows if parse_int(row.get("metrics_json_cdx_rows")) > 0
        ),
        "dynamic_metric_placeholder_games_with_alternate_endpoint_cdx_rows": sum(
            1 for row in dynamic_rows if parse_int(row.get("alternate_endpoint_cdx_rows")) > 0
        ),
        "high_value_unresolved_games": len(high_value_unresolved),
        "top_unresolved_examples": examples,
        "outputs": {
            "progress_csv": str(OUTPUT_CSV.relative_to(ROOT)),
            "report_json": str(REPORT_JSON.relative_to(ROOT)),
            "report_md": str(REPORT_MD.relative_to(ROOT)),
        },
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    status_lines = [f"- {status}: {count}" for status, count in report["status_counts"].items()]
    action_lines = [f"- {count}: {action}" for action, count in report["recommended_action_counts"].items()]
    example_lines = [
        "| {game_name} | {best_rank} | {status} | {cached_cdx_variants} | {unique_cdx_rows} | {dynamic_metric_placeholder_pages} | {metrics_json_probe_observations} | {metrics_json_cdx_rows} | {first_seen_date} |".format(
            **row
        )
        for row in examples[:25]
    ]
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Game Page Gap Progress",
                "",
                f"- Generated: {report['generated_at']}",
                f"- Profile games: {report['profile_games']}",
                f"- High-value unresolved games: {report['high_value_unresolved_games']}",
                "",
                "## Status Counts",
                "",
                *status_lines,
                "",
                "## Recommended Actions",
                "",
                *action_lines,
                "",
                "## Dynamic Placeholder Evidence",
                "",
                f"- Dynamic metric placeholder games: {report['dynamic_metric_placeholder_games']}",
                f"- With exact metrics.json probe history: {report['dynamic_metric_placeholder_games_with_metrics_json_probe']}",
                f"- With exact metrics.json CDX rows: {report['dynamic_metric_placeholder_games_with_metrics_json_cdx_rows']}",
                f"- With alternate endpoint CDX rows: {report['dynamic_metric_placeholder_games_with_alternate_endpoint_cdx_rows']}",
                "",
                "## Top Unresolved Examples",
                "",
                "| Game | Best rank | Status | Cached CDX variants | Page CDX rows | Dynamic pages | metrics.json probes | metrics.json CDX rows | First seen |",
                "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
                *example_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize cumulative game-page backfill progress for no-CDX profile games.")
    parser.add_argument("--input-csv", default=str(PROFILE_CSV), help="No-CDX profile CSV to summarize.")
    parser.add_argument("--tiers", default="1", help="Comma-separated follow-up tiers to summarize. Empty means all.")
    parser.add_argument(
        "--metrics-row-status",
        choices=["any", "no_metrics", "has_metrics"],
        default="no_metrics",
        help="Filter profile games by whether they already have per-game metrics rows.",
    )
    args = parser.parse_args()

    rows = progress_rows(args)
    write_csv(OUTPUT_CSV, rows)
    report = write_report(rows, args)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
