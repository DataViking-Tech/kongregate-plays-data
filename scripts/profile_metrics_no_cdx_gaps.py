#!/usr/bin/env python3
"""Profile no-CDX metrics-history gaps for focused follow-up."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

AUDIT_CSV = PROCESSED / "metrics_backfill_gap_audit.csv"
PROFILE_CSV = PROCESSED / "metrics_no_cdx_profile.csv"
REPORT_JSON = LOGS / "metrics_no_cdx_profile_report.json"
REPORT_MD = LOGS / "metrics_no_cdx_profile_report.md"

PROFILE_COLUMNS = [
    "followup_tier",
    "profile_bucket",
    "game_name",
    "game_url",
    "canonical_game_key",
    "best_rank",
    "top_n_appearances",
    "listing_play_count_rows",
    "first_seen_date",
    "last_seen_date",
    "recommendation",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_int(value: object) -> int:
    text = str(value or "").replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROFILE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def classify(row: dict[str, str]) -> tuple[int, str, str]:
    appearances = parse_int(row.get("top_n_appearances"))
    listing_rows = parse_int(row.get("listing_play_count_rows"))

    if listing_rows > 1 or (listing_rows > 0 and appearances > 1):
        return (
            1,
            "durable_listing_play_counts_no_metrics",
            "Review URL variants and page-history captures first; this is a repeated observed-play-count gap.",
        )
    if listing_rows == 1:
        return (
            2,
            "single_capture_listing_play_count_no_metrics",
            "Try exact-date page-history or URL-alias recovery; there is one observed listing count.",
        )
    if appearances > 1:
        return (
            3,
            "multi_capture_no_listing_counts_no_metrics",
            "Inspect source pages before deeper scraping; repeated ranking evidence exists but no play count was observed.",
        )
    return (
        4,
        "single_capture_no_listing_count_no_metrics",
        "Low-information gap; confirm the source row before spending scraper time.",
    )


def profile_rows(audit_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in audit_rows:
        if row.get("status") != "no_cdx":
            continue
        tier, bucket, recommendation = classify(row)
        rows.append(
            {
                "followup_tier": tier,
                "profile_bucket": bucket,
                "game_name": row.get("game_name", ""),
                "game_url": row.get("game_url", ""),
                "canonical_game_key": row.get("canonical_game_key", ""),
                "best_rank": parse_int(row.get("best_rank")),
                "top_n_appearances": parse_int(row.get("top_n_appearances")),
                "listing_play_count_rows": parse_int(row.get("listing_play_count_rows")),
                "first_seen_date": row.get("first_seen_date", ""),
                "last_seen_date": row.get("last_seen_date", ""),
                "recommendation": recommendation,
            }
        )
    rows.sort(
        key=lambda row: (
            row["followup_tier"],
            int(row["best_rank"]),
            -int(row["listing_play_count_rows"]),
            -int(row["top_n_appearances"]),
            str(row["first_seen_date"]),
            str(row["game_name"]).lower(),
        )
    )
    return rows


def report_for(rows: list[dict[str, object]]) -> dict[str, object]:
    bucket_counts = Counter(str(row["profile_bucket"]) for row in rows)
    year_counts = Counter(str(row["first_seen_date"])[:4] for row in rows if row["first_seen_date"])
    tier_counts = Counter(str(row["followup_tier"]) for row in rows)
    high_value = [row for row in rows if int(row["followup_tier"]) <= 2]

    return {
        "generated_at": utc_now(),
        "total_no_cdx_games": len(rows),
        "followup_tier_counts": dict(sorted(tier_counts.items(), key=lambda item: int(item[0]))),
        "profile_bucket_counts": dict(bucket_counts.most_common()),
        "first_seen_year_counts": dict(sorted(year_counts.items())),
        "high_value_followup_games": len(high_value),
        "low_information_single_capture_games": bucket_counts.get("single_capture_no_listing_count_no_metrics", 0),
        "top_high_value_examples": high_value[:40],
        "outputs": {
            "profile_csv": str(PROFILE_CSV.relative_to(ROOT)),
            "report_json": str(REPORT_JSON.relative_to(ROOT)),
            "report_md": str(REPORT_MD.relative_to(ROOT)),
        },
    }


def write_report(report: dict[str, object]) -> None:
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    bucket_lines = [
        f"- {bucket}: {count}"
        for bucket, count in report["profile_bucket_counts"].items()
    ]
    example_lines = [
        "| {game_name} | {best_rank} | {top_n_appearances} | {listing_play_count_rows} | {first_seen_date} |".format(
            **row
        )
        for row in report["top_high_value_examples"][:25]
    ]
    REPORT_MD.write_text(
        "\n".join(
            [
                "# No-CDX Metrics Gap Profile",
                "",
                f"- Generated: {report['generated_at']}",
                f"- Total no-CDX games: {report['total_no_cdx_games']}",
                f"- High-value follow-up games: {report['high_value_followup_games']}",
                f"- Low-information single-capture games: {report['low_information_single_capture_games']}",
                "",
                "## Buckets",
                "",
                *bucket_lines,
                "",
                "## Top High-Value Follow-Up Examples",
                "",
                "| Game | Best rank | Top-20 appearances | Listing play-count rows | First seen |",
                "| --- | ---: | ---: | ---: | --- |",
                *example_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    rows = profile_rows(read_csv(AUDIT_CSV))
    write_csv(PROFILE_CSV, rows)
    report = report_for(rows)
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
