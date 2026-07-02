#!/usr/bin/env python3
"""Summarize evidence for games still missing per-game play-count history."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

GAP_PROGRESS_CSV = PROCESSED / "game_page_gap_progress.csv"
LIFECYCLE_CSV = PROCESSED / "game_lifecycle_catalog.csv"
NO_CDX_PROFILE_CSV = PROCESSED / "metrics_no_cdx_profile.csv"
COUNT_SOURCE_STATUS_CSV = PROCESSED / "count_source_probe_game_status.csv"

OUTPUT_CSV = PROCESSED / "no_history_evidence_summary.csv"
REPORT_JSON = LOGS / "no_history_evidence_summary_report.json"
REPORT_MD = LOGS / "no_history_evidence_summary_report.md"

OUTPUT_COLUMNS = [
    "evidence_bucket",
    "next_recovery_track",
    "followup_tier",
    "game_name",
    "developer",
    "game_url",
    "canonical_game_key",
    "best_rank",
    "top_n_appearances",
    "first_seen_date",
    "last_seen_date",
    "listing_play_count_rows",
    "max_play_count_observed",
    "page_gap_status",
    "alternate_endpoint_cdx_rows",
    "count_source_probe_status",
    "endpoint_observations",
    "candidates_with_cdx_rows",
    "unresolved_failed_endpoints",
    "recovered_count_rows",
    "observed_categories",
    "category_tags",
    "platform_flags",
    "facebook_social_candidate",
    "classification_confidence",
    "classification_signals",
    "likely_added_date",
    "likely_added_date_confidence",
    "current_live_metric_status",
    "latest_live_metric_attempt_date",
    "removal_evidence_status",
    "removal_evidence_type",
    "observed_removed_after_date",
    "observed_removed_by_date",
    "removal_confidence",
    "profile_bucket",
    "recommended_next_action",
]


BUCKET_PRIORITIES = {
    "dynamic_placeholder_endpoint_archives_no_count": 1,
    "no_game_page_cdx_alt_archives_no_count": 2,
    "partial_listing_counts_no_page_metrics": 3,
    "dynamic_placeholder_no_exact_endpoint_archives": 4,
    "no_game_page_or_endpoint_archives": 5,
    "uncategorized_no_history_gap": 6,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_int(value: object) -> int:
    text = str(value or "").replace(",", "").strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def by_key(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["canonical_game_key"]: row for row in rows if row.get("canonical_game_key")}


def coalesce(*values: object) -> str:
    for value in values:
        text = str(value or "")
        if text:
            return text
    return ""


def classify(gap: dict[str, str], lifecycle: dict[str, str], probe: dict[str, str]) -> tuple[str, str]:
    listing_rows = max(
        parse_int(gap.get("listing_play_count_rows")),
        parse_int(lifecycle.get("listing_play_count_rows")),
    )
    page_gap_status = gap.get("status", "")
    count_source_status = coalesce(probe.get("status"), lifecycle.get("count_source_probe_status"))
    alternate_endpoint_cdx_rows = parse_int(gap.get("alternate_endpoint_cdx_rows"))

    if listing_rows > 0:
        return (
            "partial_listing_counts_no_page_metrics",
            "Carry listing counts as partial observed play-count history; keep broader source recovery for fuller timelines.",
        )
    if page_gap_status == "dynamic_metrics_placeholder" and count_source_status == "archived_endpoint_hit_no_count":
        return (
            "dynamic_placeholder_endpoint_archives_no_count",
            "Inspect archived endpoint HTML/list payloads and broaden to category, search, and developer listings.",
        )
    if page_gap_status == "no_page_cdx_rows" and alternate_endpoint_cdx_rows > 0:
        return (
            "no_game_page_cdx_alt_archives_no_count",
            "Inspect alternate archived endpoint payloads, then broaden to listings if no count text is present.",
        )
    if page_gap_status == "dynamic_metrics_placeholder":
        return (
            "dynamic_placeholder_no_exact_endpoint_archives",
            "Exact metrics and alternate endpoint probes are exhausted; move to broader archived listing/category/search sources.",
        )
    if page_gap_status == "no_page_cdx_rows":
        return (
            "no_game_page_or_endpoint_archives",
            "No exact game-page or endpoint count source remains; use ranked/listing echoes and lifecycle metadata only unless new sources are added.",
        )
    return (
        "uncategorized_no_history_gap",
        "Review manually; this row did not match the expected no-history gap states.",
    )


def build_rows() -> list[dict[str, object]]:
    gap_rows = read_csv(GAP_PROGRESS_CSV)
    lifecycle_by_key = by_key(read_csv(LIFECYCLE_CSV))
    profile_by_key = by_key(read_csv(NO_CDX_PROFILE_CSV))
    probe_by_key = by_key(read_csv(COUNT_SOURCE_STATUS_CSV))

    rows: list[dict[str, object]] = []
    for gap in gap_rows:
        key = gap.get("canonical_game_key", "")
        lifecycle = lifecycle_by_key.get(key, {})
        profile = profile_by_key.get(key, {})
        probe = probe_by_key.get(key, {})
        evidence_bucket, next_recovery_track = classify(gap, lifecycle, probe)
        rows.append(
            {
                "evidence_bucket": evidence_bucket,
                "next_recovery_track": next_recovery_track,
                "followup_tier": parse_int(gap.get("followup_tier")),
                "game_name": coalesce(lifecycle.get("game_name"), gap.get("game_name")),
                "developer": lifecycle.get("developer", ""),
                "game_url": coalesce(lifecycle.get("game_url"), gap.get("game_url")),
                "canonical_game_key": key,
                "best_rank": parse_int(coalesce(lifecycle.get("best_rank"), gap.get("best_rank"))),
                "top_n_appearances": parse_int(
                    coalesce(lifecycle.get("top_n_appearances"), gap.get("top_n_appearances"))
                ),
                "first_seen_date": coalesce(lifecycle.get("first_observed_date"), gap.get("first_seen_date")),
                "last_seen_date": coalesce(lifecycle.get("last_observed_date"), gap.get("last_seen_date")),
                "listing_play_count_rows": max(
                    parse_int(gap.get("listing_play_count_rows")),
                    parse_int(lifecycle.get("listing_play_count_rows")),
                    parse_int(profile.get("listing_play_count_rows")),
                ),
                "max_play_count_observed": parse_int(lifecycle.get("max_play_count_observed")),
                "page_gap_status": gap.get("status", ""),
                "alternate_endpoint_cdx_rows": parse_int(gap.get("alternate_endpoint_cdx_rows")),
                "count_source_probe_status": coalesce(probe.get("status"), lifecycle.get("count_source_probe_status")),
                "endpoint_observations": parse_int(probe.get("endpoint_observations")),
                "candidates_with_cdx_rows": parse_int(probe.get("candidates_with_cdx_rows")),
                "unresolved_failed_endpoints": parse_int(probe.get("unresolved_failed_endpoints")),
                "recovered_count_rows": parse_int(probe.get("recovered_count_rows")),
                "observed_categories": lifecycle.get("observed_categories", ""),
                "category_tags": lifecycle.get("category_tags", ""),
                "platform_flags": lifecycle.get("platform_flags", ""),
                "facebook_social_candidate": lifecycle.get("facebook_social_candidate", ""),
                "classification_confidence": lifecycle.get("classification_confidence", ""),
                "classification_signals": lifecycle.get("classification_signals", ""),
                "likely_added_date": lifecycle.get("likely_added_date", ""),
                "likely_added_date_confidence": lifecycle.get("likely_added_date_confidence", ""),
                "current_live_metric_status": lifecycle.get("current_live_metric_status", ""),
                "latest_live_metric_attempt_date": lifecycle.get("latest_live_metric_attempt_date", ""),
                "removal_evidence_status": lifecycle.get("removal_evidence_status", ""),
                "removal_evidence_type": lifecycle.get("removal_evidence_type", ""),
                "observed_removed_after_date": lifecycle.get("observed_removed_after_date", ""),
                "observed_removed_by_date": lifecycle.get("observed_removed_by_date", ""),
                "removal_confidence": lifecycle.get("removal_confidence", ""),
                "profile_bucket": profile.get("profile_bucket", ""),
                "recommended_next_action": gap.get("recommended_next_action", ""),
            }
        )

    rows.sort(
        key=lambda row: (
            BUCKET_PRIORITIES.get(str(row["evidence_bucket"]), 99),
            int(row["followup_tier"] or 99),
            int(row["best_rank"] or 999999),
            -int(row["top_n_appearances"] or 0),
            str(row["first_seen_date"]),
            str(row["game_name"]).lower(),
        )
    )
    return rows


def report_for(rows: list[dict[str, object]]) -> dict[str, object]:
    def counts(field: str) -> dict[str, int]:
        return dict(Counter(str(row.get(field, "")) or "blank" for row in rows).most_common())

    listing_coverage = Counter(
        "has_listing_count_observations" if parse_int(row.get("listing_play_count_rows")) else "no_listing_count_observations"
        for row in rows
    )
    added_confidence_counts = counts("likely_added_date_confidence")
    category_rows = sum(1 for row in rows if row.get("observed_categories"))
    unresolved_probe_rows = sum(parse_int(row.get("unresolved_failed_endpoints")) for row in rows)
    endpoint_hit_no_count = sum(1 for row in rows if row.get("count_source_probe_status") == "archived_endpoint_hit_no_count")
    no_endpoint_rows = sum(1 for row in rows if row.get("count_source_probe_status") == "no_archived_endpoint_rows_observed")

    return {
        "generated_at": utc_now(),
        "remaining_no_history_games": len(rows),
        "listing_count_coverage_counts": dict(listing_coverage),
        "evidence_bucket_counts": counts("evidence_bucket"),
        "page_gap_status_counts": counts("page_gap_status"),
        "count_source_probe_status_counts": counts("count_source_probe_status"),
        "current_live_metric_status_counts": counts("current_live_metric_status"),
        "removal_evidence_status_counts": counts("removal_evidence_status"),
        "facebook_social_candidate_counts": counts("facebook_social_candidate"),
        "classification_confidence_counts": counts("classification_confidence"),
        "likely_added_date_confidence_counts": added_confidence_counts,
        "rows_with_observed_categories": category_rows,
        "endpoint_hit_no_count_games": endpoint_hit_no_count,
        "no_archived_endpoint_rows_games": no_endpoint_rows,
        "unresolved_failed_endpoint_total": unresolved_probe_rows,
        "top_recovery_examples": rows[:40],
        "outputs": {
            "summary_csv": str(OUTPUT_CSV.relative_to(ROOT)),
            "report_json": str(REPORT_JSON.relative_to(ROOT)),
            "report_md": str(REPORT_MD.relative_to(ROOT)),
        },
    }


def write_report(report: dict[str, object]) -> None:
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    bucket_lines = [f"- {bucket}: {count}" for bucket, count in report["evidence_bucket_counts"].items()]
    listing_lines = [f"- {bucket}: {count}" for bucket, count in report["listing_count_coverage_counts"].items()]
    probe_lines = [f"- {status}: {count}" for status, count in report["count_source_probe_status_counts"].items()]
    example_lines = [
        "| {game_name} | {best_rank} | {listing_play_count_rows} | {page_gap_status} | {count_source_probe_status} | {likely_added_date} |".format(
            **row
        )
        for row in report["top_recovery_examples"][:25]
    ]

    REPORT_MD.write_text(
        "\n".join(
            [
                "# No-History Evidence Summary",
                "",
                f"- Generated: {report['generated_at']}",
                f"- Remaining games without per-game play-count history: {report['remaining_no_history_games']}",
                f"- Rows with observed categories: {report['rows_with_observed_categories']}",
                f"- Endpoint-hit/no-count games: {report['endpoint_hit_no_count_games']}",
                f"- No archived endpoint rows games: {report['no_archived_endpoint_rows_games']}",
                f"- Unresolved failed endpoint total: {report['unresolved_failed_endpoint_total']}",
                "",
                "## Listing Count Coverage",
                "",
                *listing_lines,
                "",
                "## Evidence Buckets",
                "",
                *bucket_lines,
                "",
                "## Count Source Probe Status",
                "",
                *probe_lines,
                "",
                "## Top Recovery Examples",
                "",
                "| Game | Best rank | Listing count rows | Page gap status | Endpoint probe status | Likely added |",
                "| --- | ---: | ---: | --- | --- | --- |",
                *example_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    rows = build_rows()
    write_csv(OUTPUT_CSV, rows)
    report = report_for(rows)
    write_report(report)
    summary = {
        "generated_at": report["generated_at"],
        "remaining_no_history_games": report["remaining_no_history_games"],
        "listing_count_coverage_counts": report["listing_count_coverage_counts"],
        "evidence_bucket_counts": report["evidence_bucket_counts"],
        "count_source_probe_status_counts": report["count_source_probe_status_counts"],
        "unresolved_failed_endpoint_total": report["unresolved_failed_endpoint_total"],
        "outputs": report["outputs"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
