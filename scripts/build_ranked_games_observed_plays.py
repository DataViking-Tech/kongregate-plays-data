#!/usr/bin/env python3
"""Build ranked rows enriched with best-known aggregate plays as of rank date."""

from __future__ import annotations

import bisect
import csv
import gzip
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from kongregate_canonical import canonical_game_url as shared_canonical_game_url


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

RANKED_CSV = PROCESSED / "ranked_games.csv"
HISTORY_CSV = PROCESSED / "game_play_history.csv"
OUTPUT_CSV = PROCESSED / "ranked_games_observed_plays.csv"
OUTPUT_CSV_GZ = PROCESSED / "ranked_games_observed_plays.csv.gz"
REPORT_JSON = LOGS / "ranked_games_observed_plays_report.json"
REPORT_MD = LOGS / "ranked_games_observed_plays_report.md"

OUTPUT_COLUMNS = [
    "date",
    "game_name",
    "rank_on_date",
    "ranking_type",
    "category",
    "game_url",
    "developer",
    "ranked_listing_plays_count",
    "ranked_listing_plays_text",
    "aggregate_plays_asof_count",
    "aggregate_plays_asof_date",
    "aggregate_plays_asof_lag_days",
    "aggregate_plays_asof_source",
    "aggregate_plays_asof_source_detail",
    "aggregate_plays_asof_capture_timestamp",
    "aggregate_plays_asof_confidence",
    "aggregate_plays_asof_method",
    "aggregate_plays_asof_staleness",
    "source_url",
    "capture_timestamp",
    "capture_url",
    "notes",
]

HISTORY_SOURCES = {"metrics_json", "live_metrics_json", "game_page_html", "count_source_probe"}


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


def write_gzip_copy(source: Path, target: Path) -> None:
    with source.open("rb") as source_handle, gzip.open(target, "wb", compresslevel=9) as target_handle:
        shutil.copyfileobj(source_handle, target_handle)


def parse_int(value: object) -> int:
    if isinstance(value, int):
        return value
    text = str(value or "").replace(",", "").strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def parse_date(value: str):
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def canonical_game_url(game_url: str) -> str:
    return shared_canonical_game_url(game_url)


def game_key(row: dict[str, str]) -> str:
    key = canonical_game_url(row.get("game_url", ""))
    if key:
        return key
    return f"{row.get('game_name', '')}|{row.get('developer', '')}".lower()


def source_detail_for_ranked(row: dict[str, str]) -> str:
    parts = [row.get("ranking_type", "ranked_listing")]
    if row.get("category"):
        parts.append(row["category"])
    if row.get("parser"):
        parts.append(row["parser"])
    return " / ".join(part for part in parts if part)


def staleness_bucket(lag_days: int | None) -> str:
    if lag_days is None:
        return ""
    if lag_days == 0:
        return "same_day"
    if lag_days <= 30:
        return "1-30_days"
    if lag_days <= 180:
        return "31-180_days"
    if lag_days <= 365:
        return "181-365_days"
    return "over_365_days"


def observation_from_ranked(row: dict[str, str], row_id: str) -> dict[str, object] | None:
    plays = parse_int(row.get("plays_count_observed"))
    if plays <= 0:
        return None
    return {
        "id": row_id,
        "date": row.get("date", ""),
        "capture_timestamp": row.get("capture_timestamp", ""),
        "plays": plays,
        "source": "ranked_listing",
        "source_detail": source_detail_for_ranked(row),
        "confidence": row.get("confidence", ""),
    }


def observation_from_history(row: dict[str, str], row_id: str) -> dict[str, object] | None:
    plays = parse_int(row.get("plays_count_observed"))
    if plays <= 0:
        return None
    parser = row.get("parser", "") or "game_play_history"
    return {
        "id": row_id,
        "date": row.get("date", ""),
        "capture_timestamp": row.get("capture_timestamp", ""),
        "plays": plays,
        "source": parser if parser in HISTORY_SOURCES else "game_play_history",
        "source_detail": row.get("metrics_url", "") or row.get("capture_url", ""),
        "confidence": row.get("confidence", ""),
    }


def build_observation_index(ranked_rows: list[dict[str, str]], history_rows: list[dict[str, str]]):
    observations_by_game: dict[str, list[dict[str, object]]] = defaultdict(list)
    for index, row in enumerate(ranked_rows):
        key = game_key(row)
        observation = observation_from_ranked(row, f"ranked:{index}")
        if key and observation:
            observations_by_game[key].append(observation)
    for index, row in enumerate(history_rows):
        key = game_key(row)
        observation = observation_from_history(row, f"history:{index}")
        if key and observation:
            observations_by_game[key].append(observation)

    indexed = {}
    for key, observations in observations_by_game.items():
        observations.sort(key=lambda item: (str(item["date"]), str(item["capture_timestamp"]), int(item["plays"])))
        dates = []
        best_observations = []
        best = None
        for observation in observations:
            if best is None or int(observation["plays"]) >= int(best["plays"]):
                best = observation
            dates.append(str(observation["date"]))
            best_observations.append(best)
        indexed[key] = (dates, best_observations)
    return indexed


def asof_observation(indexed_observations, key: str, rank_date: str) -> dict[str, object] | None:
    dates, observations = indexed_observations.get(key, ([], []))
    if not dates:
        return None
    position = bisect.bisect_right(dates, rank_date) - 1
    if position < 0:
        return None
    return observations[position]


def method_for(row_id: str, direct_count: int, observation: dict[str, object] | None) -> str:
    if not observation:
        return "no_observed_play_count_asof_rank_date"
    if direct_count > 0 and observation.get("id") == row_id:
        return "direct_listing_same_capture"
    if direct_count > 0:
        return "direct_listing_plus_prior_or_same_day_max"
    return "aggregate_asof_from_prior_observation"


def build_rows(ranked_rows: list[dict[str, str]], history_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    indexed_observations = build_observation_index(ranked_rows, history_rows)
    output_rows = []
    for index, ranked in enumerate(ranked_rows):
        row_id = f"ranked:{index}"
        key = game_key(ranked)
        rank_date = ranked.get("date", "")
        direct_count = parse_int(ranked.get("plays_count_observed"))
        observation = asof_observation(indexed_observations, key, rank_date)
        rank_day = parse_date(rank_date)
        observed_day = parse_date(str(observation.get("date", ""))) if observation else None
        lag_days = (rank_day - observed_day).days if rank_day and observed_day else None
        output_rows.append(
            {
                "date": rank_date,
                "game_name": ranked.get("game_name", ""),
                "rank_on_date": ranked.get("rank_on_date", ""),
                "ranking_type": ranked.get("ranking_type", ""),
                "category": ranked.get("category", ""),
                "game_url": ranked.get("game_url", ""),
                "developer": ranked.get("developer", ""),
                "ranked_listing_plays_count": direct_count or "",
                "ranked_listing_plays_text": ranked.get("plays_text", ""),
                "aggregate_plays_asof_count": observation.get("plays", "") if observation else "",
                "aggregate_plays_asof_date": observation.get("date", "") if observation else "",
                "aggregate_plays_asof_lag_days": lag_days if lag_days is not None else "",
                "aggregate_plays_asof_source": observation.get("source", "") if observation else "",
                "aggregate_plays_asof_source_detail": observation.get("source_detail", "") if observation else "",
                "aggregate_plays_asof_capture_timestamp": observation.get("capture_timestamp", "") if observation else "",
                "aggregate_plays_asof_confidence": observation.get("confidence", "") if observation else "",
                "aggregate_plays_asof_method": method_for(row_id, direct_count, observation),
                "aggregate_plays_asof_staleness": staleness_bucket(lag_days),
                "source_url": ranked.get("source_url", ""),
                "capture_timestamp": ranked.get("capture_timestamp", ""),
                "capture_url": ranked.get("capture_url", ""),
                "notes": (
                    "Aggregate plays are the highest observed count for this game on or before the ranked-list date; "
                    "lag fields show how stale that supporting observation is."
                ),
            }
        )
    return output_rows


def monthly_zero_count(rows: list[dict[str, object]], count_column: str) -> list[str]:
    by_month: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        month = str(row.get("date", ""))[:7]
        if month:
            by_month[month].append(row)
    zero_months = []
    for month in sorted(by_month):
        if all(parse_int(row.get(count_column)) <= 0 for row in by_month[month]):
            zero_months.append(month)
    return zero_months


def write_report(rows: list[dict[str, object]], ranked_rows: list[dict[str, str]], history_rows: list[dict[str, str]]) -> dict[str, object]:
    direct_count_rows = [row for row in rows if parse_int(row.get("ranked_listing_plays_count")) > 0]
    asof_count_rows = [row for row in rows if parse_int(row.get("aggregate_plays_asof_count")) > 0]
    lag_values = [parse_int(row.get("aggregate_plays_asof_lag_days")) for row in asof_count_rows if str(row.get("aggregate_plays_asof_lag_days", "")) != ""]
    direct_zero_months = monthly_zero_count(rows, "ranked_listing_plays_count")
    asof_zero_months = monthly_zero_count(rows, "aggregate_plays_asof_count")
    report = {
        "run_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ranked_rows": len(ranked_rows),
        "game_play_history_rows": len(history_rows),
        "rows_with_direct_listing_play_counts": len(direct_count_rows),
        "rows_with_aggregate_asof_play_counts": len(asof_count_rows),
        "direct_listing_coverage_rate": round(len(direct_count_rows) / len(rows), 4) if rows else 0,
        "aggregate_asof_coverage_rate": round(len(asof_count_rows) / len(rows), 4) if rows else 0,
        "ranked_months_without_direct_listing_play_counts": len(direct_zero_months),
        "ranked_months_without_aggregate_asof_play_counts": len(asof_zero_months),
        "direct_listing_zero_month_range": [direct_zero_months[0] if direct_zero_months else "", direct_zero_months[-1] if direct_zero_months else ""],
        "aggregate_asof_zero_month_range": [asof_zero_months[0] if asof_zero_months else "", asof_zero_months[-1] if asof_zero_months else ""],
        "aggregate_asof_method_counts": dict(Counter(str(row.get("aggregate_plays_asof_method", "")) for row in rows)),
        "aggregate_asof_source_counts": dict(Counter(str(row.get("aggregate_plays_asof_source", "")) for row in asof_count_rows)),
        "aggregate_asof_staleness_counts": dict(Counter(str(row.get("aggregate_plays_asof_staleness", "")) for row in asof_count_rows)),
        "aggregate_asof_max_lag_days": max(lag_values) if lag_values else 0,
        "outputs": {
            "csv": str(OUTPUT_CSV.relative_to(ROOT)),
            "csv_gzip": str(OUTPUT_CSV_GZ.relative_to(ROOT)),
            "report_json": str(REPORT_JSON.relative_to(ROOT)),
            "report_md": str(REPORT_MD.relative_to(ROOT)),
        },
    }
    LOGS.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2))
    direct_zero_range_label = (
        f"{report['direct_listing_zero_month_range'][0]} to {report['direct_listing_zero_month_range'][1]}"
        if report["ranked_months_without_direct_listing_play_counts"]
        else "n/a"
    )
    asof_zero_range_label = (
        f"{report['aggregate_asof_zero_month_range'][0]} to {report['aggregate_asof_zero_month_range'][1]}"
        if report["ranked_months_without_aggregate_asof_play_counts"]
        else "n/a"
    )
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Ranked Games Observed Plays Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- Ranked rows: {report['ranked_rows']}",
                f"- Direct listing play-count rows: {report['rows_with_direct_listing_play_counts']} ({report['direct_listing_coverage_rate']:.2%})",
                f"- Aggregate as-of play-count rows: {report['rows_with_aggregate_asof_play_counts']} ({report['aggregate_asof_coverage_rate']:.2%})",
                f"- Ranked months with rows but no direct listing play counts: {report['ranked_months_without_direct_listing_play_counts']} ({direct_zero_range_label})",
                f"- Ranked months with rows but no aggregate as-of play counts: {report['ranked_months_without_aggregate_asof_play_counts']} ({asof_zero_range_label})",
                f"- Max aggregate as-of observation lag: {report['aggregate_asof_max_lag_days']} days",
                "",
                "The output keeps the raw ranked-list play count separate from the aggregate as-of count. The aggregate count is the highest observed count for that game on or before the ranked-list date, not an interpolated estimate.",
                "",
            ]
        )
    )
    return report


def main() -> None:
    ranked_rows = read_csv(RANKED_CSV)
    history_rows = read_csv(HISTORY_CSV)
    rows = build_rows(ranked_rows, history_rows)
    write_csv(OUTPUT_CSV, rows)
    write_gzip_copy(OUTPUT_CSV, OUTPUT_CSV_GZ)
    report = write_report(rows, ranked_rows, history_rows)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
