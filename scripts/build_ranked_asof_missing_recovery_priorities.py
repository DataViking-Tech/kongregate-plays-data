#!/usr/bin/env python3
"""Build a game-level recovery queue for ranked rows without as-of play counts."""

from __future__ import annotations

import csv
import gzip
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from kongregate_canonical import canonical_game_url as shared_canonical_game_url


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

RANKED_OBSERVED_CSV = PROCESSED / "ranked_games_observed_plays.csv"
RANKED_OBSERVED_GZ = PROCESSED / "ranked_games_observed_plays.csv.gz"
HISTORY_CSV = PROCESSED / "game_play_history.csv"
MINI_CATALOG_CSV = PROCESSED / "mini_catalog.csv"
METRICS_AUDIT_CSV = PROCESSED / "metrics_backfill_gap_audit.csv"
NO_HISTORY_SUMMARY_CSV = PROCESSED / "no_history_evidence_summary.csv"

OUTPUT_CSV = PROCESSED / "ranked_asof_missing_recovery_priorities.csv"
REPORT_JSON = LOGS / "ranked_asof_missing_recovery_report.json"
REPORT_MD = LOGS / "ranked_asof_missing_recovery_report.md"

OUTPUT_COLUMNS = [
    "priority_rank",
    "recovery_priority_score",
    "recovery_class",
    "recommended_recovery_track",
    "canonical_game_key",
    "game_name",
    "developer",
    "game_url",
    "in_mini_catalog",
    "missing_rank_rows",
    "rank1_missing_rows",
    "top5_missing_rows",
    "top10_missing_rows",
    "top20_missing_rows",
    "best_missing_rank",
    "first_missing_rank_date",
    "last_missing_rank_date",
    "missing_rank_span_days",
    "ranking_types_with_missing",
    "categories_with_missing",
    "sample_missing_dates",
    "has_any_observed_play_count",
    "first_observed_play_count_date",
    "first_observed_play_count",
    "first_observed_play_count_source",
    "first_observed_after_first_missing_days",
    "first_observed_after_last_missing_days",
    "latest_observed_play_count_date",
    "latest_observed_play_count",
    "missing_rows_on_or_after_first_observation",
    "catalog_first_seen_date",
    "catalog_last_seen_date",
    "catalog_best_rank",
    "catalog_top_n_appearances",
    "catalog_listing_play_count_rows",
    "catalog_max_listing_play_count_observed",
    "metrics_status",
    "metrics_rows",
    "first_metric_date",
    "last_metric_date",
    "no_history_evidence_bucket",
    "page_gap_status",
    "count_source_probe_status",
    "alternate_endpoint_cdx_rows",
    "endpoint_observations",
    "candidates_with_cdx_rows",
    "recovered_count_rows",
    "current_live_metric_status",
    "observed_categories",
    "platform_flags",
    "classification_confidence",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_game_url(game_url: str) -> str:
    return shared_canonical_game_url(game_url)


def game_key(row: dict[str, str]) -> str:
    return canonical_game_url(row.get("game_url", ""))


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


def parse_date(value: object):
    text = str(value or "")[:10]
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def date_diff_days(later: str, earlier: str) -> int | str:
    later_date = parse_date(later)
    earlier_date = parse_date(earlier)
    if not later_date or not earlier_date:
        return ""
    return (later_date - earlier_date).days


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_ranked_observed_rows() -> list[dict[str, str]]:
    if RANKED_OBSERVED_CSV.exists():
        return read_csv(RANKED_OBSERVED_CSV)
    if not RANKED_OBSERVED_GZ.exists():
        return []
    with gzip.open(RANKED_OBSERVED_GZ, "rt", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in OUTPUT_COLUMNS} for row in rows)


def most_common_join(values: list[str], limit: int = 8) -> str:
    counter = Counter(value for value in values if value)
    return "; ".join(f"{value} ({count})" for value, count in counter.most_common(limit))


def first_nonempty(rows: list[dict[str, str]], key: str) -> str:
    for row in rows:
        value = row.get(key, "")
        if value:
            return value
    return ""


def load_lookup(path: Path) -> dict[str, dict[str, str]]:
    lookup = {}
    for row in read_csv(path):
        key = row.get("canonical_game_key") or canonical_game_url(row.get("game_url", ""))
        if key:
            lookup[key] = row
    return lookup


def ranked_observations_by_game(ranked_rows: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    observations: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in ranked_rows:
        plays = parse_int(row.get("ranked_listing_plays_count"))
        if plays <= 0:
            continue
        key = game_key(row)
        if not key:
            continue
        observations[key].append(
            {
                "date": row.get("date", ""),
                "plays": plays,
                "source": "ranked_listing",
                "capture_timestamp": row.get("capture_timestamp", ""),
            }
        )
    return observations


def history_observations_by_game() -> dict[str, list[dict[str, object]]]:
    observations: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in read_csv(HISTORY_CSV):
        plays = parse_int(row.get("plays_count_observed"))
        if plays <= 0:
            continue
        key = game_key(row)
        if not key:
            continue
        observations[key].append(
            {
                "date": row.get("date", ""),
                "plays": plays,
                "source": row.get("parser", "game_play_history"),
                "capture_timestamp": row.get("capture_timestamp", ""),
            }
        )
    return observations


def combined_observations(ranked_rows: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    observations = ranked_observations_by_game(ranked_rows)
    for key, rows in history_observations_by_game().items():
        observations[key].extend(rows)
    for rows in observations.values():
        rows.sort(key=lambda row: (str(row.get("date", "")), str(row.get("capture_timestamp", "")), int(row.get("plays") or 0)))
    return observations


def priority_score(missing_count: int, rank1: int, top5: int, top10: int, best_rank: int, has_observation: bool) -> int:
    rank_bonus = max(0, 21 - best_rank) * 25 if best_rank else 0
    no_count_bonus = 300 if not has_observation else 0
    return missing_count * 10 + rank1 * 1000 + top5 * 250 + top10 * 100 + rank_bonus + no_count_bonus


def recovery_class_and_track(
    has_observation: bool,
    first_observed_date: str,
    last_missing_date: str,
    identity_review_rows: int,
    in_mini_catalog: bool,
    no_history: dict[str, str],
) -> tuple[str, str]:
    if has_observation:
        if identity_review_rows:
            return (
                "identity_or_date_mismatch_review",
                "Review canonical URL aliases or date parsing; at least one missing row is on/after the first observed count date.",
            )
        return (
            "earlier_history_needed",
            "Search earlier game-page, metrics, developer/account-list, and category/list captures before the first observed play count.",
        )

    if not in_mini_catalog:
        return (
            "outside_mini_catalog_scope_no_count",
            "Outside the top-20 mini-catalog scope; profile only if broadening recovery beyond games that reached the top 20.",
        )

    page_status = no_history.get("page_gap_status", "")
    bucket = no_history.get("evidence_bucket", "")
    if page_status == "dynamic_metrics_placeholder":
        return (
            "no_count_dynamic_placeholder",
            "Broaden alternate source shapes; archived game pages defer counts to unarchived metrics.json endpoints.",
        )
    if page_status == "no_page_cdx_rows":
        return (
            "no_count_no_page_cdx",
            "Try broader URL variants, developer/account lists, search/category pages, or external evidence; checked game-page variants have no usable CDX rows.",
        )
    if bucket:
        return ("no_count_profiled_other", no_history.get("next_recovery_track", "Continue alternate count-source exploration."))
    return ("no_count_unprofiled", "Add this game to no-history profiling and probe page/list/source variants.")


def build_rows() -> tuple[list[dict[str, object]], dict[str, object]]:
    ranked_rows = read_ranked_observed_rows()
    missing_rows_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ranked_rows:
        if parse_int(row.get("aggregate_plays_asof_count")) > 0:
            continue
        key = game_key(row)
        if key:
            missing_rows_by_key[key].append(row)

    observations_by_key = combined_observations(ranked_rows)
    catalog_by_key = load_lookup(MINI_CATALOG_CSV)
    audit_by_key = load_lookup(METRICS_AUDIT_CSV)
    no_history_by_key = load_lookup(NO_HISTORY_SUMMARY_CSV)

    rows: list[dict[str, object]] = []
    for key, missing_rows in missing_rows_by_key.items():
        dates = sorted(row.get("date", "") for row in missing_rows if row.get("date"))
        ranks = [parse_int(row.get("rank_on_date")) for row in missing_rows if parse_int(row.get("rank_on_date")) > 0]
        best_missing_rank = min(ranks) if ranks else 0
        rank1 = sum(1 for rank in ranks if rank == 1)
        top5 = sum(1 for rank in ranks if 1 <= rank <= 5)
        top10 = sum(1 for rank in ranks if 1 <= rank <= 10)
        top20 = sum(1 for rank in ranks if 1 <= rank <= 20)
        first_missing = dates[0] if dates else ""
        last_missing = dates[-1] if dates else ""

        observations = observations_by_key.get(key, [])
        first_observed = observations[0] if observations else {}
        latest_observed = max(observations, key=lambda row: (str(row.get("date", "")), int(row.get("plays") or 0))) if observations else {}
        first_observed_date = str(first_observed.get("date", ""))
        identity_review_rows = 0
        if first_observed_date:
            identity_review_rows = sum(1 for row in missing_rows if row.get("date", "") >= first_observed_date)

        catalog = catalog_by_key.get(key, {})
        audit = audit_by_key.get(key, {})
        no_history = no_history_by_key.get(key, {})
        in_mini_catalog = bool(catalog)
        has_observation = bool(observations)
        recovery_class, track = recovery_class_and_track(
            has_observation,
            first_observed_date,
            last_missing,
            identity_review_rows,
            in_mini_catalog,
            no_history,
        )
        game_name = catalog.get("game_name") or first_nonempty(missing_rows, "game_name")
        game_url = catalog.get("game_url") or first_nonempty(missing_rows, "game_url")
        developer = catalog.get("developer") or first_nonempty(missing_rows, "developer")

        rows.append(
            {
                "recovery_priority_score": priority_score(len(missing_rows), rank1, top5, top10, best_missing_rank, has_observation),
                "recovery_class": recovery_class,
                "recommended_recovery_track": track,
                "canonical_game_key": key,
                "game_name": game_name,
                "developer": developer,
                "game_url": game_url,
                "in_mini_catalog": "yes" if in_mini_catalog else "no",
                "missing_rank_rows": len(missing_rows),
                "rank1_missing_rows": rank1,
                "top5_missing_rows": top5,
                "top10_missing_rows": top10,
                "top20_missing_rows": top20,
                "best_missing_rank": best_missing_rank or "",
                "first_missing_rank_date": first_missing,
                "last_missing_rank_date": last_missing,
                "missing_rank_span_days": date_diff_days(last_missing, first_missing),
                "ranking_types_with_missing": most_common_join([row.get("ranking_type", "") for row in missing_rows]),
                "categories_with_missing": most_common_join([row.get("category", "") for row in missing_rows]),
                "sample_missing_dates": "; ".join(dates[:8]),
                "has_any_observed_play_count": "yes" if has_observation else "no",
                "first_observed_play_count_date": first_observed_date,
                "first_observed_play_count": first_observed.get("plays", ""),
                "first_observed_play_count_source": first_observed.get("source", ""),
                "first_observed_after_first_missing_days": date_diff_days(first_observed_date, first_missing) if first_observed_date else "",
                "first_observed_after_last_missing_days": date_diff_days(first_observed_date, last_missing) if first_observed_date else "",
                "latest_observed_play_count_date": latest_observed.get("date", ""),
                "latest_observed_play_count": latest_observed.get("plays", ""),
                "missing_rows_on_or_after_first_observation": identity_review_rows,
                "catalog_first_seen_date": catalog.get("first_seen_date", ""),
                "catalog_last_seen_date": catalog.get("last_seen_date", ""),
                "catalog_best_rank": catalog.get("best_rank", ""),
                "catalog_top_n_appearances": catalog.get("top_n_appearances", ""),
                "catalog_listing_play_count_rows": catalog.get("listing_play_count_rows", ""),
                "catalog_max_listing_play_count_observed": catalog.get("max_listing_play_count_observed", ""),
                "metrics_status": audit.get("status", ""),
                "metrics_rows": audit.get("metrics_rows", ""),
                "first_metric_date": audit.get("first_metric_date", ""),
                "last_metric_date": audit.get("last_metric_date", ""),
                "no_history_evidence_bucket": no_history.get("evidence_bucket", ""),
                "page_gap_status": no_history.get("page_gap_status", ""),
                "count_source_probe_status": no_history.get("count_source_probe_status", ""),
                "alternate_endpoint_cdx_rows": no_history.get("alternate_endpoint_cdx_rows", ""),
                "endpoint_observations": no_history.get("endpoint_observations", ""),
                "candidates_with_cdx_rows": no_history.get("candidates_with_cdx_rows", ""),
                "recovered_count_rows": no_history.get("recovered_count_rows", ""),
                "current_live_metric_status": no_history.get("current_live_metric_status", ""),
                "observed_categories": no_history.get("observed_categories", ""),
                "platform_flags": no_history.get("platform_flags", ""),
                "classification_confidence": no_history.get("classification_confidence", ""),
            }
        )

    rows.sort(
        key=lambda row: (
            -parse_int(row.get("recovery_priority_score")),
            -parse_int(row.get("missing_rank_rows")),
            parse_int(row.get("best_missing_rank")) or 999999,
            str(row.get("first_missing_rank_date")),
            str(row.get("game_name", "")).lower(),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["priority_rank"] = index

    report = build_report(rows, ranked_rows)
    return rows, report


def build_report(rows: list[dict[str, object]], ranked_rows: list[dict[str, str]]) -> dict[str, object]:
    class_counts = Counter(str(row.get("recovery_class", "")) for row in rows)
    missing_rank_rows = sum(parse_int(row.get("missing_rank_rows")) for row in rows)
    no_observation_games = sum(1 for row in rows if row.get("has_any_observed_play_count") == "no")
    later_observation_games = sum(1 for row in rows if row.get("has_any_observed_play_count") == "yes")
    top_rows = [
        {
            "priority_rank": row.get("priority_rank"),
            "game_name": row.get("game_name"),
            "missing_rank_rows": row.get("missing_rank_rows"),
            "best_missing_rank": row.get("best_missing_rank"),
            "first_missing_rank_date": row.get("first_missing_rank_date"),
            "last_missing_rank_date": row.get("last_missing_rank_date"),
            "recovery_class": row.get("recovery_class"),
            "first_observed_play_count_date": row.get("first_observed_play_count_date"),
            "first_observed_play_count": row.get("first_observed_play_count"),
        }
        for row in rows[:25]
    ]
    return {
        "run_timestamp": utc_now(),
        "ranked_rows": len(ranked_rows),
        "missing_rank_rows_without_aggregate_asof_count": missing_rank_rows,
        "games_with_missing_asof_rank_rows": len(rows),
        "games_with_later_or_other_observed_counts": later_observation_games,
        "games_with_no_observed_play_count_anywhere": no_observation_games,
        "recovery_class_counts": dict(class_counts.most_common()),
        "top_priority_games": top_rows,
        "outputs": {
            "priority_csv": str(OUTPUT_CSV.relative_to(ROOT)),
            "report_json": str(REPORT_JSON.relative_to(ROOT)),
            "report_md": str(REPORT_MD.relative_to(ROOT)),
        },
    }


def write_report(report: dict[str, object]) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Ranked As-Of Missing Recovery Report",
        "",
        f"- Run timestamp: {report['run_timestamp']}",
        f"- Ranked rows: {report['ranked_rows']}",
        f"- Missing rank rows without aggregate as-of count: {report['missing_rank_rows_without_aggregate_asof_count']}",
        f"- Games with missing as-of rank rows: {report['games_with_missing_asof_rank_rows']}",
        f"- Games with later or other observed counts: {report['games_with_later_or_other_observed_counts']}",
        f"- Games with no observed play count anywhere: {report['games_with_no_observed_play_count_anywhere']}",
        "",
        "## Recovery Classes",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in report["recovery_class_counts"].items())
    lines.extend(
        [
            "",
            "## Top Priority Games",
            "",
            "| Rank | Game | Missing rows | Best missing rank | Missing date range | Class | First observed count |",
            "| ---: | --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in report["top_priority_games"]:
        count_label = ""
        if row.get("first_observed_play_count_date"):
            count_label = f"{int(row.get('first_observed_play_count') or 0):,} on {row.get('first_observed_play_count_date')}"
        lines.append(
            "| {priority_rank} | {game_name} | {missing_rank_rows} | {best_missing_rank} | {first_missing_rank_date} to {last_missing_rank_date} | {recovery_class} | {count_label} |".format(
                count_label=count_label,
                **row,
            )
        )
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows, report = build_rows()
    write_csv(OUTPUT_CSV, rows)
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
