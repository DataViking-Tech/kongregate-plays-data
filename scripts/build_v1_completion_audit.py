#!/usr/bin/env python3
"""Build a v1 completion/readiness audit from the current Kongregate reports."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
LOGS = ROOT / "logs"
OUTPUT_CSV = DATA / "v1_completion_audit.csv"
REPORT_JSON = LOGS / "v1_completion_audit_report.json"
REPORT_MD = LOGS / "v1_completion_audit_report.md"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def pct(numerator: int, denominator: int) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator * 100, 2)


def int_value(value: object) -> int:
    try:
        return int(float(str(value or "0").replace(",", "")))
    except ValueError:
        return 0


def finalization_bucket(priority: dict[str, str], feasibility: dict[str, str]) -> tuple[str, str]:
    recovery_class = priority.get("recovery_class", "")
    exact_status = feasibility.get("exact_metrics_gap_status", "")
    no_history_bucket = priority.get("no_history_evidence_bucket", "")
    page_gap_status = priority.get("page_gap_status", "")

    if recovery_class == "earlier_history_needed":
        if exact_status == "exact_metrics_starts_after_missing_window":
            return (
                "earlier_history_exact_metrics_start_after_gap",
                "Known later count exists, but exact archived metrics begin after the missing rank window.",
            )
        if exact_status == "exact_metrics_no_cached_cdx_rows":
            return (
                "earlier_history_no_exact_metrics_archives",
                "Known later count exists, but exact archived metrics routes have no usable CDX rows for the missing window.",
            )
        if exact_status:
            return (
                f"earlier_history_{exact_status}",
                "Known later count exists, but exact archived metrics evidence is not usable for the missing window.",
            )
        return (
            "earlier_history_unclassified_exact_metrics",
            "Known later count exists; exact metrics feasibility has not produced a stronger bucket.",
        )

    if recovery_class == "no_count_dynamic_placeholder":
        if no_history_bucket == "dynamic_placeholder_endpoint_archives_no_count":
            return (
                "no_count_dynamic_placeholder_endpoint_archives_no_count",
                "Archived game pages defer counts to dynamic metrics; alternate endpoint archives exist but no public count was parsed.",
            )
        return (
            "no_count_dynamic_placeholder_no_count_source",
            "Archived game pages defer counts to dynamic metrics and no count-bearing archive has been found.",
        )

    if recovery_class == "no_count_no_page_cdx":
        return (
            "no_count_no_page_cdx",
            "Checked game-page URL variants have no usable CDX rows; no count-bearing archive has been found.",
        )

    if recovery_class == "outside_mini_catalog_scope_no_count":
        return (
            "outside_mini_catalog_scope_no_count",
            "Ranked-row gap sits outside the current top-20 mini-catalog recovery scope.",
        )

    if page_gap_status:
        return (
            f"unclassified_with_page_gap_{page_gap_status}",
            "Remaining gap is classified by page-gap status but not by recovery class.",
        )

    return ("unclassified_remaining_gap", "Remaining gap needs manual review.")


def recommended_disposition(bucket: str) -> str:
    if bucket.startswith("earlier_history_"):
        return (
            "Call complete for Kongregate/Wayback v1 unless this game is analytically critical; "
            "further recovery likely needs broader list/account captures or external corroboration."
        )
    if bucket.startswith("no_count_dynamic_placeholder"):
        return (
            "Call complete for Kongregate/Wayback v1 with explicit no-count evidence; "
            "archived pages defer to unavailable dynamic metrics."
        )
    if bucket == "no_count_no_page_cdx":
        return (
            "Call complete for Kongregate/Wayback v1 with explicit no-page-CDX evidence; "
            "further recovery likely needs external sources."
        )
    if bucket == "outside_mini_catalog_scope_no_count":
        return "Leave as out-of-scope for mini-catalog v1 unless the scope expands beyond top-20 games."
    return "Manual review before v1 closure."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-through-priority-rank", type=int, default=189)
    args = parser.parse_args()

    data_quality = read_json(LOGS / "data_quality_report.json")
    count_source = read_json(LOGS / "count_source_probe_history_report.json")
    no_history = read_json(LOGS / "no_history_evidence_summary_report.json")
    page_gap = read_json(LOGS / "game_page_gap_progress_report.json")
    lifecycle = read_json(LOGS / "game_lifecycle_catalog_report.json")

    priorities = read_rows(DATA / "ranked_asof_missing_recovery_priorities.csv")
    feasibility_rows = {
        row.get("canonical_game_key", ""): row
        for row in read_rows(DATA / "asof_recovery_feasibility_audit.csv")
    }

    audit_rows: list[dict[str, object]] = []
    for row in priorities:
        feasibility = feasibility_rows.get(row.get("canonical_game_key", ""), {})
        bucket, evidence_summary = finalization_bucket(row, feasibility)
        audit_rows.append(
            {
                "priority_rank": int_value(row.get("priority_rank")),
                "game_name": row.get("game_name", ""),
                "developer": row.get("developer", ""),
                "canonical_game_key": row.get("canonical_game_key", ""),
                "missing_rank_rows": int_value(row.get("missing_rank_rows")),
                "best_missing_rank": int_value(row.get("best_missing_rank")),
                "first_missing_rank_date": row.get("first_missing_rank_date", ""),
                "last_missing_rank_date": row.get("last_missing_rank_date", ""),
                "recovery_class": row.get("recovery_class", ""),
                "exact_metrics_gap_status": feasibility.get("exact_metrics_gap_status", ""),
                "page_gap_status": row.get("page_gap_status", ""),
                "no_history_evidence_bucket": row.get("no_history_evidence_bucket", ""),
                "count_source_probe_status": row.get("count_source_probe_status", ""),
                "side_endpoint_cdx_hit_observations": int_value(feasibility.get("side_endpoint_cdx_hit_observations")),
                "developer_list_observations": int_value(feasibility.get("developer_list_observations")),
                "first_observed_play_count_date": row.get("first_observed_play_count_date", ""),
                "first_observed_play_count_source": row.get("first_observed_play_count_source", ""),
                "v1_finalization_bucket": bucket,
                "v1_evidence_summary": evidence_summary,
                "v1_disposition": recommended_disposition(bucket),
            }
        )

    fields = [
        "priority_rank",
        "game_name",
        "developer",
        "canonical_game_key",
        "missing_rank_rows",
        "best_missing_rank",
        "first_missing_rank_date",
        "last_missing_rank_date",
        "recovery_class",
        "exact_metrics_gap_status",
        "page_gap_status",
        "no_history_evidence_bucket",
        "count_source_probe_status",
        "side_endpoint_cdx_hit_observations",
        "developer_list_observations",
        "first_observed_play_count_date",
        "first_observed_play_count_source",
        "v1_finalization_bucket",
        "v1_evidence_summary",
        "v1_disposition",
    ]
    write_rows(OUTPUT_CSV, audit_rows, fields)

    bucket_counts = Counter(row["v1_finalization_bucket"] for row in audit_rows)
    recovery_counts = Counter(row["recovery_class"] for row in audit_rows)
    remaining_priority_games = max(0, len(priorities) - args.processed_through_priority_rank)
    checks = {
        "ranked_months_without_aggregate_asof_play_counts_is_zero": int_value(
            data_quality.get("ranked_months_without_aggregate_asof_play_counts")
        )
        == 0,
        "play_count_decreases_is_zero": int_value(data_quality.get("play_count_decreases")) == 0,
        "no_history_unresolved_failed_endpoint_total_is_zero": int_value(
            no_history.get("unresolved_failed_endpoint_total")
        )
        == 0,
        "all_priority_rows_have_v1_bucket": all(
            row["v1_finalization_bucket"] != "unclassified_remaining_gap" for row in audit_rows
        ),
    }
    ready = all(checks.values())

    report = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "v1_recommendation": "ready_to_call_kongregate_wayback_v1_after_public_note" if ready else "needs_review_before_v1",
        "v1_checks": checks,
        "coverage": {
            "ranked_rows": data_quality.get("ranked_rows"),
            "ranked_rows_with_aggregate_asof_play_counts": data_quality.get(
                "ranked_rows_with_aggregate_asof_play_counts"
            ),
            "ranked_rows_without_aggregate_asof_play_count": data_quality.get(
                "ranked_rows_without_aggregate_asof_play_count"
            ),
            "aggregate_asof_coverage_pct": pct(
                int_value(data_quality.get("ranked_rows_with_aggregate_asof_play_counts")),
                int_value(data_quality.get("ranked_rows")),
            ),
            "catalog_games": data_quality.get("catalog_games"),
            "metrics_history_games": data_quality.get("metrics_history_games"),
            "catalog_games_without_metrics_history": data_quality.get("catalog_games_without_metrics_history"),
            "catalog_history_coverage_pct": pct(
                int_value(data_quality.get("metrics_history_games")),
                int_value(data_quality.get("catalog_games")),
            ),
            "ranked_date_range": data_quality.get("ranked_date_range"),
            "metrics_history_date_range": data_quality.get("metrics_history_date_range"),
        },
        "remaining_workload_math": {
            "priority_games": len(priorities),
            "processed_through_priority_rank": args.processed_through_priority_rank,
            "remaining_priority_games_if_five_game_slices_continue": remaining_priority_games,
            "remaining_five_game_slices": math.ceil(remaining_priority_games / 5) if remaining_priority_games else 0,
        },
        "finalization_bucket_counts": dict(sorted(bucket_counts.items())),
        "recovery_class_counts": dict(sorted(recovery_counts.items())),
        "no_history_evidence_bucket_counts": no_history.get("evidence_bucket_counts", {}),
        "count_source_probe_status_counts": count_source.get("status_counts", {}),
        "page_gap_status_counts": page_gap.get("status_counts", {}),
        "lifecycle": {
            "rows_with_observed_categories": lifecycle.get("rows_with_observed_categories"),
            "rows_with_published_dates": lifecycle.get("rows_with_published_dates"),
            "facebook_social_candidate_counts": lifecycle.get("facebook_social_candidate_counts"),
            "removal_evidence_status_counts": lifecycle.get("removal_evidence_status_counts"),
        },
        "top_remaining_examples": audit_rows[:25],
        "outputs": {
            "audit_csv": str(OUTPUT_CSV.relative_to(ROOT)),
            "report_json": str(REPORT_JSON.relative_to(ROOT)),
            "report_md": str(REPORT_MD.relative_to(ROOT)),
        },
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Kongregate V1 Completion Audit",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Recommendation: `{report['v1_recommendation']}`",
        f"- Aggregate as-of coverage: {report['coverage']['ranked_rows_with_aggregate_asof_play_counts']} / {report['coverage']['ranked_rows']} ({report['coverage']['aggregate_asof_coverage_pct']}%)",
        f"- Remaining ranked rows without aggregate as-of count: {report['coverage']['ranked_rows_without_aggregate_asof_play_count']}",
        f"- Catalog play-history coverage: {report['coverage']['metrics_history_games']} / {report['coverage']['catalog_games']} ({report['coverage']['catalog_history_coverage_pct']}%)",
        f"- Continuing the old five-game cadence would require about {report['remaining_workload_math']['remaining_five_game_slices']} more slices.",
        "",
        "## V1 Checks",
        "",
    ]
    for check, passed in checks.items():
        lines.append(f"- {'PASS' if passed else 'REVIEW'}: {check}")

    lines.extend(["", "## Finalization Buckets", ""])
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- {bucket}: {count}")

    lines.extend(["", "## Top Remaining Examples", ""])
    for row in audit_rows[:25]:
        lines.append(
            f"- #{row['priority_rank']} {row['game_name']} ({row['missing_rank_rows']} rows, best rank {row['best_missing_rank']}): {row['v1_finalization_bucket']}"
        )

    lines.extend(["", "## Outputs", "", f"- `{report['outputs']['audit_csv']}`", f"- `{report['outputs']['report_json']}`"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
