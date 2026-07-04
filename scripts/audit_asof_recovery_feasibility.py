#!/usr/bin/env python3
"""Audit remaining as-of play-count gaps against cached endpoint evidence."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from kongregate_canonical import canonical_game_url
from fetch_game_metrics_history import cdx_cache_path as game_metrics_cdx_cache_path
from probe_archived_count_sources import cdx_cache_path as count_probe_cdx_cache_path
from probe_archived_count_sources import game_path_from_url, path_to_urls


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

PRIORITIES_CSV = PROCESSED / "ranked_asof_missing_recovery_priorities.csv"
PROGRESS_CSV = PROCESSED / "ranked_asof_game_page_probe_progress.csv"
PROBE_HISTORY_CSV = PROCESSED / "count_source_probe_history.csv"
COUNT_SOURCE_CSV = PROCESSED / "count_source_play_counts.csv"
AUDIT_CSV = PROCESSED / "asof_recovery_feasibility_audit.csv"
REPORT_JSON = LOGS / "asof_recovery_feasibility_audit_report.json"
REPORT_MD = LOGS / "asof_recovery_feasibility_audit_report.md"

SIDE_ENDPOINT_TYPES = {"holodeck", "chat_js", "chat_achievements", "recommended_games", "game_path_prefix"}

AUDIT_COLUMNS = [
    "priority_rank",
    "game_name",
    "game_url",
    "canonical_game_key",
    "missing_rank_rows",
    "best_missing_rank",
    "first_missing_rank_date",
    "last_missing_rank_date",
    "first_observed_play_count_date",
    "first_observed_play_count_source",
    "page_gap_status",
    "metrics_status",
    "exact_metrics_endpoint_count",
    "exact_metrics_cdx_rows",
    "exact_metrics_cached_endpoint_count",
    "exact_metrics_missing_cache_count",
    "exact_metrics_first_cdx_date",
    "exact_metrics_last_cdx_date",
    "exact_metrics_cdx_rows_in_missing_window",
    "exact_metrics_sampled_rows_in_missing_window",
    "exact_metrics_parsed_rows",
    "exact_metrics_first_parsed_date",
    "exact_metrics_first_parsed_plays",
    "exact_metrics_gap_status",
    "side_endpoint_observations",
    "side_endpoint_cdx_hit_observations",
    "side_endpoint_rows_in_missing_window",
    "side_endpoint_parsed_rows",
    "developer_list_observations",
    "developer_list_rows_in_missing_window",
    "recommended_next_action",
]


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
        writer = csv.DictWriter(handle, fieldnames=AUDIT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_int(value: object) -> int:
    try:
        return int(str(value or "0").replace(",", ""))
    except ValueError:
        return 0


def date_from_timestamp(value: str) -> str:
    text = str(value or "")
    if len(text) >= 8 and text[:8].isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return ""


def in_date_window(date_value: str, start: str, end: str) -> bool:
    return bool(date_value and start and end and start <= date_value <= end)


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_rows_by_key(path: Path) -> dict[str, list[dict[str, str]]]:
    rows_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(path):
        key = row.get("canonical_game_key") or canonical_game_url(row.get("game_url", ""))
        if key:
            rows_by_key[key].append(row)
    return rows_by_key


def metrics_endpoints(game_url: str, history_rows: list[dict[str, str]]) -> list[str]:
    endpoints = [row.get("endpoint_url", "") for row in history_rows if row.get("source_type") == "metrics_json"]
    game_path = game_path_from_url(game_url)
    if game_path:
        endpoints.extend(path_to_urls(f"{game_path}/metrics.json", game_url))
    return [endpoint for endpoint in dict.fromkeys(endpoints) if endpoint]


def cached_exact_cdx_rows(endpoints: list[str]) -> tuple[list[dict[str, str]], int, int]:
    rows_by_identity: dict[tuple[str, str], dict[str, str]] = {}
    cached_endpoint_count = 0
    missing_cache_count = 0
    for endpoint in endpoints:
        cache_paths = [
            count_probe_cdx_cache_path(endpoint, "exact"),
            game_metrics_cdx_cache_path(endpoint),
        ]
        existing_paths = [path for path in cache_paths if path.exists()]
        if not existing_paths:
            missing_cache_count += 1
            continue
        cached_endpoint_count += 1
        endpoint_had_readable_cache = False
        for path in existing_paths:
            try:
                rows = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            endpoint_had_readable_cache = True
            for row in rows:
                timestamp = row.get("timestamp", "")
                original = row.get("original", "")
                if timestamp and original:
                    rows_by_identity[(timestamp, original)] = row
        if not endpoint_had_readable_cache:
            missing_cache_count += 1
    return sorted(rows_by_identity.values(), key=lambda row: (row.get("timestamp", ""), row.get("original", ""))), cached_endpoint_count, missing_cache_count


def first_parsed_count(rows: list[dict[str, str]]) -> tuple[str, str]:
    parsed = sorted(
        (
            (date_from_timestamp(row.get("sample_timestamp", "")), row.get("parsed_plays", ""))
            for row in rows
            if parse_int(row.get("parsed_plays")) > 0 and date_from_timestamp(row.get("sample_timestamp", ""))
        ),
        key=lambda item: item[0],
    )
    return parsed[0] if parsed else ("", "")


def classify_exact_metrics(cdx_rows: list[dict[str, str]], overlap_count: int, sampled_overlap_count: int, parsed_rows: int, first_missing: str, last_missing: str) -> str:
    if not cdx_rows:
        return "exact_metrics_no_cached_cdx_rows"
    cdx_dates = [date_from_timestamp(row.get("timestamp", "")) for row in cdx_rows]
    cdx_dates = [date for date in cdx_dates if date]
    first_cdx = min(cdx_dates) if cdx_dates else ""
    last_cdx = max(cdx_dates) if cdx_dates else ""
    if overlap_count:
        if parsed_rows:
            return "exact_metrics_overlap_with_later_count_signal"
        if sampled_overlap_count:
            return "exact_metrics_overlap_sampled_no_count_signal"
        return "exact_metrics_overlap_unsampled"
    if first_cdx and last_missing and first_cdx > last_missing:
        return "exact_metrics_starts_after_missing_window"
    if last_cdx and first_missing and last_cdx < first_missing:
        return "exact_metrics_only_before_missing_window"
    return "exact_metrics_outside_missing_window"


def recommended_action(row: dict[str, object]) -> str:
    status = str(row["exact_metrics_gap_status"])
    side_hits = parse_int(row["side_endpoint_cdx_hit_observations"])
    side_counts = parse_int(row["side_endpoint_parsed_rows"])
    missing_cache = parse_int(row["exact_metrics_missing_cache_count"])
    sampled_overlap = parse_int(row["exact_metrics_sampled_rows_in_missing_window"])
    if status == "exact_metrics_overlap_unsampled":
        return "Sample exact metrics.json captures inside the missing rank window."
    if status == "exact_metrics_overlap_sampled_no_count_signal":
        return "Treat exact metrics as weak for this window; inspect payload schema only if this game is strategically important."
    if status == "exact_metrics_starts_after_missing_window":
        if side_hits and not side_counts:
            return "Exact metrics start too late and side endpoints lack public counts; pursue list/account captures or external corroboration."
        return "Exact metrics start too late; pursue broader list/account captures or external corroboration."
    if status == "exact_metrics_no_cached_cdx_rows":
        if missing_cache:
            return "Run a bounded exact metrics CDX check before escalating."
        return "Escalate to broader list/account captures or external corroboration."
    if status == "exact_metrics_overlap_with_later_count_signal":
        return "Review exact metrics samples; count signal exists but does not yet close the as-of gap."
    return "Use lower-priority broad page-history/list recovery unless this game is analytically important."


def main() -> None:
    priority_rows = read_csv(PRIORITIES_CSV)
    progress_by_key = {row.get("canonical_game_key") or canonical_game_url(row.get("game_url", "")): row for row in read_csv(PROGRESS_CSV)}
    history_by_key = load_rows_by_key(PROBE_HISTORY_CSV)
    count_by_key = load_rows_by_key(COUNT_SOURCE_CSV)

    audit_rows: list[dict[str, object]] = []
    for priority in priority_rows:
        key = priority.get("canonical_game_key") or canonical_game_url(priority.get("game_url", ""))
        if not key:
            continue
        first_missing = priority.get("first_missing_rank_date", "")
        last_missing = priority.get("last_missing_rank_date", "")
        history_rows = history_by_key.get(key, [])
        count_rows = count_by_key.get(key, [])
        progress = progress_by_key.get(key, {})

        endpoints = metrics_endpoints(priority.get("game_url", ""), history_rows)
        exact_cdx_rows, cached_endpoint_count, missing_cache_count = cached_exact_cdx_rows(endpoints)
        cdx_dates = [date_from_timestamp(row.get("timestamp", "")) for row in exact_cdx_rows]
        cdx_dates = [date for date in cdx_dates if date]
        exact_overlap_count = sum(1 for date in cdx_dates if in_date_window(date, first_missing, last_missing))

        metrics_history_rows = [row for row in history_rows if row.get("source_type") == "metrics_json"]
        metrics_sampled_overlap = sum(
            1
            for row in metrics_history_rows
            if in_date_window(date_from_timestamp(row.get("sample_timestamp", "")), first_missing, last_missing)
        )
        metrics_count_rows = [row for row in count_rows if row.get("source_type") == "metrics_json"]
        first_parsed_date, first_parsed_plays = first_parsed_count(metrics_count_rows)

        side_rows = [row for row in history_rows if row.get("source_type") in SIDE_ENDPOINT_TYPES]
        side_hit_rows = [row for row in side_rows if parse_int(row.get("cdx_rows")) > 0]
        side_overlap = sum(
            1
            for row in side_rows
            if in_date_window(date_from_timestamp(row.get("sample_timestamp", "")), first_missing, last_missing)
        )
        side_count_rows = [row for row in count_rows if row.get("source_type") in SIDE_ENDPOINT_TYPES]
        developer_rows = [row for row in history_rows if row.get("source_type") == "developer_game_list"]
        developer_overlap = sum(
            1
            for row in developer_rows
            if in_date_window(date_from_timestamp(row.get("sample_timestamp", "")), first_missing, last_missing)
        )

        row = {
            "priority_rank": priority.get("priority_rank", ""),
            "game_name": priority.get("game_name", ""),
            "game_url": priority.get("game_url", ""),
            "canonical_game_key": key,
            "missing_rank_rows": priority.get("missing_rank_rows", ""),
            "best_missing_rank": priority.get("best_missing_rank", ""),
            "first_missing_rank_date": first_missing,
            "last_missing_rank_date": last_missing,
            "first_observed_play_count_date": priority.get("first_observed_play_count_date", ""),
            "first_observed_play_count_source": priority.get("first_observed_play_count_source", ""),
            "page_gap_status": progress.get("status", priority.get("page_gap_status", "")),
            "metrics_status": priority.get("metrics_status", ""),
            "exact_metrics_endpoint_count": len(endpoints),
            "exact_metrics_cdx_rows": len(exact_cdx_rows),
            "exact_metrics_cached_endpoint_count": cached_endpoint_count,
            "exact_metrics_missing_cache_count": missing_cache_count,
            "exact_metrics_first_cdx_date": min(cdx_dates) if cdx_dates else "",
            "exact_metrics_last_cdx_date": max(cdx_dates) if cdx_dates else "",
            "exact_metrics_cdx_rows_in_missing_window": exact_overlap_count,
            "exact_metrics_sampled_rows_in_missing_window": metrics_sampled_overlap,
            "exact_metrics_parsed_rows": len(metrics_count_rows),
            "exact_metrics_first_parsed_date": first_parsed_date,
            "exact_metrics_first_parsed_plays": first_parsed_plays,
            "exact_metrics_gap_status": classify_exact_metrics(
                exact_cdx_rows,
                exact_overlap_count,
                metrics_sampled_overlap,
                len(metrics_count_rows),
                first_missing,
                last_missing,
            ),
            "side_endpoint_observations": len(side_rows),
            "side_endpoint_cdx_hit_observations": len(side_hit_rows),
            "side_endpoint_rows_in_missing_window": side_overlap,
            "side_endpoint_parsed_rows": len(side_count_rows),
            "developer_list_observations": len(developer_rows),
            "developer_list_rows_in_missing_window": developer_overlap,
            "recommended_next_action": "",
        }
        row["recommended_next_action"] = recommended_action(row)
        audit_rows.append(row)

    audit_rows.sort(
        key=lambda row: (
            parse_int(row.get("priority_rank")) or 999999,
            -parse_int(row.get("missing_rank_rows")),
            str(row.get("game_name", "")).lower(),
        )
    )
    write_csv(AUDIT_CSV, audit_rows)

    status_counts = Counter(str(row["exact_metrics_gap_status"]) for row in audit_rows)
    action_counts = Counter(str(row["recommended_next_action"]) for row in audit_rows)
    top_exact_overlap_unsampled = [row for row in audit_rows if row["exact_metrics_gap_status"] == "exact_metrics_overlap_unsampled"][:25]
    top_exact_starts_late = [row for row in audit_rows if row["exact_metrics_gap_status"] == "exact_metrics_starts_after_missing_window"][:25]
    report = {
        "generated_at": utc_now(),
        "priority_rows": len(audit_rows),
        "exact_metrics_gap_status_counts": dict(sorted(status_counts.items())),
        "recommended_action_counts": dict(action_counts.most_common()),
        "top_exact_metrics_overlap_unsampled": top_exact_overlap_unsampled,
        "top_exact_metrics_starts_after_missing_window": top_exact_starts_late,
        "outputs": {
            "csv": relative(AUDIT_CSV),
            "report_json": relative(REPORT_JSON),
            "report_md": relative(REPORT_MD),
        },
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# As-Of Recovery Feasibility Audit",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Ranked as-of gap rows audited: {report['priority_rows']}",
        "",
        "## Exact Metrics Gap Status",
        "",
    ]
    for status, count in status_counts.most_common():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Recommended Actions", ""])
    for action, count in action_counts.most_common():
        lines.append(f"- {action}: {count}")
    lines.extend(["", "## Top Exact Metrics Overlap, Unsampled", ""])
    if top_exact_overlap_unsampled:
        for row in top_exact_overlap_unsampled[:15]:
            lines.append(
                f"- {row['game_name']}: {row['missing_rank_rows']} missing rows, "
                f"{row['exact_metrics_cdx_rows_in_missing_window']} exact metrics CDX rows in window "
                f"({row['first_missing_rank_date']} to {row['last_missing_rank_date']})."
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## Top Exact Metrics Starts After Missing Window", ""])
    for row in top_exact_starts_late[:15]:
        lines.append(
            f"- {row['game_name']}: {row['missing_rank_rows']} missing rows; "
            f"missing window ends {row['last_missing_rank_date']}, first exact metrics CDX row is {row['exact_metrics_first_cdx_date'] or 'unknown'}."
        )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
