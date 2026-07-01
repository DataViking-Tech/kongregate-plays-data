#!/usr/bin/env python3
"""Summarize accumulated alternate play-count source probes."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from kongregate_canonical import canonical_game_url


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

PROFILE_CSV = PROCESSED / "metrics_no_cdx_profile.csv"
HISTORY_CSV = PROCESSED / "count_source_probe_history.csv"
PLAY_COUNTS_CSV = PROCESSED / "count_source_play_counts.csv"
GAME_STATUS_CSV = PROCESSED / "count_source_probe_game_status.csv"
REPORT_JSON = LOGS / "count_source_probe_history_report.json"
REPORT_MD = LOGS / "count_source_probe_history_report.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_int(value: object) -> int:
    try:
        return int(str(value or "0").replace(",", ""))
    except ValueError:
        return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def status_for_game(rows: list[dict[str, str]], recovered_rows: list[dict[str, str]]) -> str:
    if recovered_rows:
        return "recovered_count"
    if not rows:
        return "not_probed"
    if any(parse_int(row.get("cdx_rows")) > 0 for row in rows):
        return "archived_endpoint_hit_no_count"
    if any(str(row.get("cdx_status", "")).startswith("failed") for row in rows):
        return "transient_failures_remaining"
    return "no_archived_endpoint_rows_observed"


def main() -> None:
    profile_rows = read_csv(PROFILE_CSV)
    history_rows = read_csv(HISTORY_CSV)
    recovered_rows = read_csv(PLAY_COUNTS_CSV)

    profile_by_key: dict[str, dict[str, str]] = {}
    for row in profile_rows:
        key = row.get("canonical_game_key") or canonical_game_url(row.get("game_url", ""))
        if key:
            profile_by_key[key] = row

    history_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in history_rows:
        key = canonical_game_url(row.get("game_url", ""))
        if key:
            history_by_key[key].append(row)

    recovered_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in recovered_rows:
        key = canonical_game_url(row.get("game_url", ""))
        if key:
            recovered_by_key[key].append(row)

    status_rows: list[dict[str, object]] = []
    all_keys = set(profile_by_key) | set(history_by_key) | set(recovered_by_key)
    for key in sorted(all_keys):
        profile = profile_by_key.get(key, {})
        rows = history_by_key.get(key, [])
        recovered = recovered_by_key.get(key, [])
        cdx_hits = [row for row in rows if parse_int(row.get("cdx_rows")) > 0]
        failed = [row for row in rows if str(row.get("cdx_status", "")).startswith("failed")]
        parsed = [row for row in rows if parse_int(row.get("parsed_plays")) > 0]
        status_rows.append(
            {
                "status": status_for_game(rows, recovered or parsed),
                "followup_tier": profile.get("followup_tier", ""),
                "game_name": profile.get("game_name") or (rows[0].get("game_name", "") if rows else recovered[0].get("game_name", "")),
                "game_url": profile.get("game_url") or (rows[0].get("game_url", "") if rows else recovered[0].get("game_url", "")),
                "canonical_game_key": key,
                "best_rank": profile.get("best_rank", ""),
                "first_seen_date": profile.get("first_seen_date", ""),
                "endpoint_observations": len(rows),
                "candidates_with_cdx_rows": len(cdx_hits),
                "failed_observations": len(failed),
                "parsed_probe_count_rows": len(parsed),
                "recovered_count_rows": len(recovered),
                "source_types_seen": ";".join(sorted({row.get("source_type", "") for row in rows if row.get("source_type", "")})),
                "latest_probe_run_timestamp": max((row.get("last_probe_run_timestamp", "") for row in rows), default=""),
            }
        )

    status_rows.sort(
        key=lambda row: (
            parse_int(row.get("followup_tier")) or 99,
            parse_int(row.get("best_rank")) or 999999,
            str(row.get("first_seen_date", "")),
            str(row.get("game_name", "")).lower(),
        )
    )

    GAME_STATUS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with GAME_STATUS_CSV.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(status_rows[0].keys()) if status_rows else [
            "status",
            "followup_tier",
            "game_name",
            "game_url",
            "canonical_game_key",
            "best_rank",
            "first_seen_date",
            "endpoint_observations",
            "candidates_with_cdx_rows",
            "failed_observations",
            "parsed_probe_count_rows",
            "recovered_count_rows",
            "source_types_seen",
            "latest_probe_run_timestamp",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(status_rows)

    status_counts = Counter(str(row["status"]) for row in status_rows)
    tier1_rows = [row for row in status_rows if str(row.get("followup_tier")) == "1"]
    report = {
        "run_timestamp": utc_now(),
        "profile_games": len(profile_by_key),
        "history_observation_rows": len(history_rows),
        "history_games": len(history_by_key),
        "recovered_count_rows": len(recovered_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "tier1_status_counts": dict(sorted(Counter(str(row["status"]) for row in tier1_rows).items())),
        "cdx_status_counts": dict(sorted(Counter(row.get("cdx_status", "").split(":", 1)[0] or "unknown" for row in history_rows).items())),
        "source_type_counts": dict(sorted(Counter(row.get("source_type", "") or "unknown" for row in history_rows).items())),
        "top_unprobed": [row for row in status_rows if row["status"] == "not_probed"][:25],
        "top_transient_failures": [row for row in status_rows if row["status"] == "transient_failures_remaining"][:25],
        "outputs": {
            "game_status_csv": relative(GAME_STATUS_CSV),
            "history_csv": relative(HISTORY_CSV),
            "play_counts_csv": relative(PLAY_COUNTS_CSV),
            "report_json": relative(REPORT_JSON),
            "report_md": relative(REPORT_MD),
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Count Source Probe History",
        "",
        f"- Generated: {report['run_timestamp']}",
        f"- Profile games tracked: {report['profile_games']}",
        f"- Accumulated endpoint observations: {report['history_observation_rows']}",
        f"- Games with probe history: {report['history_games']}",
        f"- Recovered count rows: {report['recovered_count_rows']}",
        f"- Status counts: {', '.join(f'{key}={value}' for key, value in report['status_counts'].items()) or 'none'}",
        f"- Tier-1 status counts: {', '.join(f'{key}={value}' for key, value in report['tier1_status_counts'].items()) or 'none'}",
        f"- CDX status counts: {', '.join(f'{key}={value}' for key, value in report['cdx_status_counts'].items()) or 'none'}",
        "",
    ]
    if report["top_transient_failures"]:
        lines.extend(["## Retry Queue", "", "| Game | Rank | Failed | Observations | Latest Probe |", "| --- | ---: | ---: | ---: | --- |"])
        for row in report["top_transient_failures"][:15]:
            lines.append(
                f"| {row['game_name']} | {row['best_rank'] or 'n/a'} | {row['failed_observations']} | {row['endpoint_observations']} | {row['latest_probe_run_timestamp']} |"
            )
        lines.append("")
    if report["top_unprobed"]:
        lines.extend(["## Top Unprobed Profile Games", "", "| Game | Rank | First Seen |", "| --- | ---: | --- |"])
        for row in report["top_unprobed"][:15]:
            lines.append(f"| {row['game_name']} | {row['best_rank'] or 'n/a'} | {row['first_seen_date']} |")
        lines.append("")
    lines.extend(
        [
            "## Output Files",
            "",
            f"- `{report['outputs']['game_status_csv']}`",
            f"- `{report['outputs']['history_csv']}`",
            f"- `{report['outputs']['play_counts_csv']}`",
            f"- `{report['outputs']['report_json']}`",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
