#!/usr/bin/env python3
"""Scan processed Kongregate scrape outputs for coverage gaps and inconsistencies."""

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.parse
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"
RAW_HTML = ROOT / "data" / "raw" / "html"
CHART_JSON = ROOT / "outputs" / "kongregate_ranked_games" / "play_count_bar_chart_race_data.json"

RANKED_CSV = PROCESSED / "ranked_games.csv"
CATALOG_CSV = PROCESSED / "mini_catalog.csv"
HISTORY_CSV = PROCESSED / "game_play_history.csv"

ISSUES_CSV = PROCESSED / "data_quality_issues.csv"
COVERAGE_BY_YEAR_CSV = PROCESSED / "coverage_by_year.csv"
CATALOG_PRIORITIES_CSV = PROCESSED / "catalog_history_priorities.csv"
FINAL_CHART_STALENESS_CSV = PROCESSED / "final_chart_staleness.csv"
PLAY_COUNT_DECREASES_CSV = PROCESSED / "play_count_decreases.csv"
STALE_LISTING_COUNTS_CSV = PROCESSED / "stale_listing_play_counts.csv"
REPORT_JSON = LOGS / "data_quality_report.json"
REPORT_MD = LOGS / "data_quality_report.md"


ISSUE_COLUMNS = ["severity", "area", "issue_type", "count", "first_date", "last_date", "example", "recommended_action"]
COVERAGE_COLUMNS = [
    "year",
    "ranked_rows",
    "ranked_rows_with_play_counts",
    "ranked_play_count_rate",
    "metrics_rows",
    "metrics_games",
    "unique_ranked_games",
]
PRIORITY_COLUMNS = [
    "priority_score",
    "game_name",
    "game_url",
    "best_rank",
    "top_n_appearances",
    "listing_play_count_rows",
    "needs_game_page_history",
    "metrics_rows",
    "first_metric_date",
    "last_metric_date",
    "first_seen_date",
    "last_seen_date",
]
STALENESS_COLUMNS = ["rank", "game_name", "game_url", "plays", "last_observed_date", "days_stale", "source"]
DECREASE_COLUMNS = [
    "game_name",
    "game_url",
    "previous_date",
    "previous_plays",
    "current_date",
    "current_plays",
    "drop",
    "current_source",
]
STALE_LISTING_COLUMNS = [
    *DECREASE_COLUMNS,
    "first_seen_date",
    "first_seen_source",
    "reason",
]


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


def parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def parse_int(value: object) -> int:
    if isinstance(value, int):
        return value
    text = str(value or "").replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def is_likely_listing_rounding_drop(previous_plays: int, current_plays: int, previous_source: str, current_source: str) -> bool:
    if current_plays <= 0:
        return False
    drop = previous_plays - current_plays
    if drop <= 0:
        return False
    tolerance = max(100_000, int(previous_plays * 0.05))
    current_is_rounded_listing = current_source != "metrics_json" and current_plays >= 1_000_000 and current_plays % 100_000 == 0
    previous_is_rounded_listing = previous_source != "metrics_json" and previous_plays >= 1_000_000 and previous_plays % 100_000 == 0
    return (current_is_rounded_listing or previous_is_rounded_listing) and drop <= tolerance


def canonical_game_url(game_url: str) -> str:
    if not game_url:
        return ""
    parsed = urllib.parse.urlsplit(game_url)
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/]+)", parsed.path)
    if not match:
        return game_url.lower()
    developer, slug = match.groups()
    return f"www.kongregate.com/games/{urllib.parse.unquote(developer)}/{urllib.parse.unquote(slug)}".lower()


def html_text_is_valid(text: str) -> bool:
    if not text.strip():
        return False
    prefix = text[:4096]
    cleaned = prefix.lstrip("\ufeff\x00\x1f\ufffd\r\n\t ")
    lowered = cleaned[:1200].lower()
    return (
        lowered.startswith("<!doctype")
        or lowered.startswith("<html")
        or lowered.startswith("<turbo-frame")
        or "<html" in lowered
        or "<body" in lowered
    )


def invalid_cached_html_files() -> list[Path]:
    if not RAW_HTML.exists():
        return []
    invalid = []
    for path in sorted(RAW_HTML.glob("*.html")):
        if path.stat().st_size <= 0 or not html_text_is_valid(path.read_text(errors="replace")):
            invalid.append(path)
    return invalid


def month_range(start: date, end: date) -> list[str]:
    months = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return months


def issue(severity: str, area: str, issue_type: str, count: int, first_date: str, last_date: str, example: str, recommended_action: str) -> dict[str, object]:
    return {
        "severity": severity,
        "area": area,
        "issue_type": issue_type,
        "count": count,
        "first_date": first_date,
        "last_date": last_date,
        "example": example,
        "recommended_action": recommended_action,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan processed Kongregate scrape outputs for coverage gaps and inconsistencies.")
    parser.add_argument("--as-of", default=datetime.now(timezone.utc).date().isoformat(), help="As-of date for staleness calculations.")
    args = parser.parse_args()

    as_of = parse_date(args.as_of) or datetime.now(timezone.utc).date()
    ranked_rows = read_csv(RANKED_CSV)
    catalog_rows = read_csv(CATALOG_CSV)
    history_rows = read_csv(HISTORY_CSV)
    invalid_html_paths = invalid_cached_html_files()

    ranked_dates = [parse_date(row.get("date", "")) for row in ranked_rows]
    ranked_dates = [value for value in ranked_dates if value]
    history_dates = [parse_date(row.get("date", "")) for row in history_rows]
    history_dates = [value for value in history_dates if value]

    ranked_with_counts = [row for row in ranked_rows if parse_int(row.get("plays_count_observed")) > 0]
    bad_title_rows = [
        row
        for row in ranked_rows
        if re.match(r"^\d[\d,.]*\s*[kmb]?\s+(?:gameplays|plays|played)\b", row.get("game_name", ""), flags=re.I)
    ]
    missing_url_rows = [row for row in ranked_rows if not row.get("game_url")]
    missing_name_rows = [row for row in ranked_rows if not row.get("game_name")]

    duplicate_keys = Counter(
        (
            row.get("date", ""),
            row.get("source_url", ""),
            row.get("rank_on_date", ""),
            canonical_game_url(row.get("game_url", "")),
        )
        for row in ranked_rows
    )
    duplicate_count = sum(count - 1 for count in duplicate_keys.values() if count > 1)

    raw_urls_by_canonical: dict[str, set[str]] = defaultdict(set)
    for row in ranked_rows + history_rows:
        key = canonical_game_url(row.get("game_url", ""))
        if key:
            raw_urls_by_canonical[key].add(row.get("game_url", ""))
    url_variant_games = {key: urls for key, urls in raw_urls_by_canonical.items() if len(urls) > 1}

    ranked_by_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    ranked_counts_by_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    ranked_games_by_year: dict[str, set[str]] = defaultdict(set)
    for row in ranked_rows:
        row_date = parse_date(row.get("date", ""))
        if not row_date:
            continue
        year = str(row_date.year)
        ranked_by_year[year].append(row)
        ranked_games_by_year[year].add(canonical_game_url(row.get("game_url", "")) or row.get("game_name", ""))
        if parse_int(row.get("plays_count_observed")) > 0:
            ranked_counts_by_year[year].append(row)

    metrics_by_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    metrics_games_by_year: dict[str, set[str]] = defaultdict(set)
    metrics_by_game: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in history_rows:
        row_date = parse_date(row.get("date", ""))
        key = canonical_game_url(row.get("game_url", ""))
        if not row_date or not key:
            continue
        year = str(row_date.year)
        metrics_by_year[year].append(row)
        metrics_games_by_year[year].add(key)
        metrics_by_game[key].append(row)

    all_years = sorted({*ranked_by_year.keys(), *metrics_by_year.keys()})
    coverage_rows = []
    for year in all_years:
        ranked_total = len(ranked_by_year[year])
        ranked_count_total = len(ranked_counts_by_year[year])
        coverage_rows.append(
            {
                "year": year,
                "ranked_rows": ranked_total,
                "ranked_rows_with_play_counts": ranked_count_total,
                "ranked_play_count_rate": round(ranked_count_total / ranked_total, 4) if ranked_total else 0,
                "metrics_rows": len(metrics_by_year[year]),
                "metrics_games": len(metrics_games_by_year[year]),
                "unique_ranked_games": len(ranked_games_by_year[year]),
            }
        )

    ranked_months = {row["date"][:7] for row in ranked_rows if row.get("date")}
    zero_months: list[str] = []
    if ranked_dates:
        for month in month_range(min(ranked_dates), as_of):
            if month not in ranked_months:
                zero_months.append(month)

    priority_rows = []
    for row in catalog_rows:
        key = canonical_game_url(row.get("game_url", ""))
        metric_rows = metrics_by_game.get(key, [])
        metric_dates = sorted(parse_date(item.get("date", "")) for item in metric_rows)
        metric_dates = [value for value in metric_dates if value]
        best_rank = parse_int(row.get("best_rank"))
        appearances = parse_int(row.get("top_n_appearances"))
        listing_rows = parse_int(row.get("listing_play_count_rows"))
        needs_history = row.get("needs_game_page_history", "")
        priority_score = 0
        priority_score += max(0, 25 - best_rank) * 100
        priority_score += min(appearances, 250)
        if not metric_rows:
            priority_score += 500
        if needs_history == "yes":
            priority_score += 300
        elif needs_history == "partial":
            priority_score += 150
        if listing_rows == 0:
            priority_score += 150
        priority_rows.append(
            {
                "priority_score": priority_score,
                "game_name": row.get("game_name", ""),
                "game_url": row.get("game_url", ""),
                "best_rank": best_rank,
                "top_n_appearances": appearances,
                "listing_play_count_rows": listing_rows,
                "needs_game_page_history": needs_history,
                "metrics_rows": len(metric_rows),
                "first_metric_date": metric_dates[0].isoformat() if metric_dates else "",
                "last_metric_date": metric_dates[-1].isoformat() if metric_dates else "",
                "first_seen_date": row.get("first_seen_date", ""),
                "last_seen_date": row.get("last_seen_date", ""),
            }
        )
    priority_rows.sort(key=lambda row: (-int(row["priority_score"]), int(row["best_rank"] or 999999), row["game_name"].lower()))

    chart_payload = {}
    if CHART_JSON.exists():
        chart_payload = json.loads(CHART_JSON.read_text())
    frames = chart_payload.get("frames", [])
    final_entries = frames[-1].get("entries", []) if frames else []
    staleness_rows = []
    for entry in final_entries:
        last_observed = parse_date(entry.get("lastObservedDate", ""))
        days_stale = (as_of - last_observed).days if last_observed else 0
        staleness_rows.append(
            {
                "rank": entry.get("rank", ""),
                "game_name": entry.get("gameName", ""),
                "game_url": entry.get("gameUrl", ""),
                "plays": entry.get("plays", ""),
                "last_observed_date": entry.get("lastObservedDate", ""),
                "days_stale": days_stale,
                "source": entry.get("source", ""),
            }
        )

    observations_by_game: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in ranked_rows:
        plays = parse_int(row.get("plays_count_observed"))
        key = canonical_game_url(row.get("game_url", ""))
        if plays > 0 and key:
            observations_by_game[key].append({**row, "plays": plays, "source": row.get("ranking_type", "ranked"), "sort_date": row.get("date", "")})
    for row in history_rows:
        plays = parse_int(row.get("plays_count_observed"))
        key = canonical_game_url(row.get("game_url", ""))
        if plays > 0 and key:
            observations_by_game[key].append({**row, "plays": plays, "source": "metrics_json", "sort_date": row.get("date", "")})

    decrease_rows = []
    stale_listing_rows = []
    for key, rows in observations_by_game.items():
        rows.sort(key=lambda row: (str(row.get("sort_date", "")), str(row.get("capture_timestamp", ""))))
        previous = None
        first_seen_by_count = {}
        for row in rows:
            if previous and int(row["plays"]) < int(previous["plays"]):
                stale_match = first_seen_by_count.get(int(row["plays"]))
                if stale_match and str(row.get("source", "")) != "metrics_json":
                    stale_listing_rows.append(
                        {
                            "game_name": row.get("game_name", ""),
                            "game_url": row.get("game_url", ""),
                            "previous_date": previous.get("sort_date", ""),
                            "previous_plays": previous.get("plays", ""),
                            "current_date": row.get("sort_date", ""),
                            "current_plays": row.get("plays", ""),
                            "drop": int(previous["plays"]) - int(row["plays"]),
                            "current_source": row.get("source", ""),
                            "first_seen_date": stale_match.get("sort_date", ""),
                            "first_seen_source": stale_match.get("source", ""),
                            "reason": "Listing page repeated an older already-observed play count after a higher count was observed.",
                        }
                    )
                elif not is_likely_listing_rounding_drop(int(previous["plays"]), int(row["plays"]), str(previous.get("source", "")), str(row.get("source", ""))):
                    decrease_rows.append(
                        {
                            "game_name": row.get("game_name", ""),
                            "game_url": row.get("game_url", ""),
                            "previous_date": previous.get("sort_date", ""),
                            "previous_plays": previous.get("plays", ""),
                            "current_date": row.get("sort_date", ""),
                            "current_plays": row.get("plays", ""),
                            "drop": int(previous["plays"]) - int(row["plays"]),
                            "current_source": row.get("source", ""),
                        }
                    )
            if not previous or int(row["plays"]) >= int(previous["plays"]):
                previous = row
            first_seen_by_count.setdefault(int(row["plays"]), row)
    decrease_rows.sort(key=lambda row: int(row["drop"]), reverse=True)
    stale_listing_rows.sort(key=lambda row: int(row["drop"]), reverse=True)

    issues = []
    if ranked_dates:
        last_ranked_date = max(ranked_dates)
        days_since_ranked = (as_of - last_ranked_date).days
        if days_since_ranked > 45:
            issues.append(issue("high", "coverage", "ranked_capture_lag", days_since_ranked, last_ranked_date.isoformat(), as_of.isoformat(), "latest ranked row", "Run modern ranked-page discovery/fetch for the newest Wayback captures."))
    if invalid_html_paths:
        issues.append(issue("high", "cache", "invalid_cached_html_files", len(invalid_html_paths), "", "", str(invalid_html_paths[0].relative_to(ROOT)), "Retry affected captures; these files are empty or corrupted and cannot be parsed."))
    if zero_months:
        issues.append(issue("medium", "coverage", "months_without_ranked_captures", len(zero_months), zero_months[0], zero_months[-1], ", ".join(zero_months[:8]), "Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches."))
    games_without_metrics = [row for row in priority_rows if int(row["metrics_rows"]) == 0]
    if games_without_metrics:
        issues.append(issue("high", "metrics", "catalog_games_without_metrics_history", len(games_without_metrics), "", "", games_without_metrics[0]["game_name"], "Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit."))
    partial_or_missing_listing = [row for row in catalog_rows if row.get("needs_game_page_history") in {"yes", "partial"}]
    if partial_or_missing_listing:
        issues.append(issue("high", "metrics", "catalog_games_need_page_history", len(partial_or_missing_listing), "", "", partial_or_missing_listing[0].get("game_name", ""), "Continue per-game metrics history backfill."))
    stale_final = [row for row in staleness_rows if parse_int(row["days_stale"]) > 365]
    if stale_final:
        issues.append(issue("high", "chart", "final_top_chart_entries_stale_over_one_year", len(stale_final), "", "", stale_final[0]["game_name"], "Prioritize metrics histories for stale high-play games still dominating final chart ranks."))
    if bad_title_rows:
        issues.append(issue("high", "parser", "play_count_text_used_as_game_name", len(bad_title_rows), bad_title_rows[0].get("date", ""), bad_title_rows[-1].get("date", ""), bad_title_rows[0].get("game_name", ""), "Fix parser/title selector and re-extract."))
    if missing_url_rows:
        issues.append(issue("medium", "parser", "ranked_rows_missing_game_url", len(missing_url_rows), "", "", missing_url_rows[0].get("game_name", ""), "Inspect parser coverage for layouts where title was found without URL."))
    if missing_name_rows:
        issues.append(issue("medium", "parser", "ranked_rows_missing_game_name", len(missing_name_rows), "", "", missing_name_rows[0].get("game_url", ""), "Inspect parser title extraction."))
    if duplicate_count:
        issues.append(issue("low", "dedupe", "duplicate_ranked_rows", duplicate_count, "", "", "", "Review duplicate key handling by date/source/rank/game."))
    if url_variant_games:
        first_key, first_urls = next(iter(url_variant_games.items()))
        issues.append(issue("medium", "identity", "games_with_multiple_url_variants", len(url_variant_games), "", "", f"{first_key}: {sorted(first_urls)[:3]}", "Use canonical URL keys for joins and charting; consider canonicalizing processed rows."))
    if decrease_rows:
        issues.append(issue("medium", "plays", "play_count_decreases", len(decrease_rows), decrease_rows[-1].get("current_date", ""), decrease_rows[0].get("current_date", ""), decrease_rows[0].get("game_name", ""), "Review source-specific decreases; chart uses max observed counts but raw rows need QA labels."))
    if stale_listing_rows:
        issues.append(issue("low", "plays", "stale_listing_play_count_observations", len(stale_listing_rows), stale_listing_rows[-1].get("current_date", ""), stale_listing_rows[0].get("current_date", ""), stale_listing_rows[0].get("game_name", ""), "Kept as raw observations, but excluded from true decrease counts because the value repeats an older listing count."))

    write_csv(ISSUES_CSV, ISSUE_COLUMNS, issues)
    write_csv(COVERAGE_BY_YEAR_CSV, COVERAGE_COLUMNS, coverage_rows)
    write_csv(CATALOG_PRIORITIES_CSV, PRIORITY_COLUMNS, priority_rows)
    write_csv(FINAL_CHART_STALENESS_CSV, STALENESS_COLUMNS, staleness_rows)
    write_csv(PLAY_COUNT_DECREASES_CSV, DECREASE_COLUMNS, decrease_rows)
    write_csv(STALE_LISTING_COUNTS_CSV, STALE_LISTING_COLUMNS, stale_listing_rows)

    report = {
        "run_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "as_of": as_of.isoformat(),
        "ranked_rows": len(ranked_rows),
        "ranked_rows_with_play_counts": len(ranked_with_counts),
        "ranked_date_range": [min(ranked_dates).isoformat() if ranked_dates else "", max(ranked_dates).isoformat() if ranked_dates else ""],
        "catalog_games": len(catalog_rows),
        "metrics_history_rows": len(history_rows),
        "metrics_history_games": len(metrics_by_game),
        "metrics_history_date_range": [min(history_dates).isoformat() if history_dates else "", max(history_dates).isoformat() if history_dates else ""],
        "zero_ranked_capture_months": len(zero_months),
        "catalog_games_without_metrics_history": len(games_without_metrics),
        "catalog_games_need_page_history": len(partial_or_missing_listing),
        "final_chart_entries_stale_over_one_year": len(stale_final),
        "invalid_cached_html_files": len(invalid_html_paths),
        "invalid_cached_html_examples": [str(path.relative_to(ROOT)) for path in invalid_html_paths[:12]],
        "bad_title_rows": len(bad_title_rows),
        "missing_url_rows": len(missing_url_rows),
        "duplicate_ranked_rows": duplicate_count,
        "games_with_multiple_url_variants": len(url_variant_games),
        "play_count_decreases": len(decrease_rows),
        "stale_listing_play_count_observations": len(stale_listing_rows),
        "issues": issues,
        "outputs": {
            "issues_csv": str(ISSUES_CSV.relative_to(ROOT)),
            "coverage_by_year_csv": str(COVERAGE_BY_YEAR_CSV.relative_to(ROOT)),
            "catalog_priorities_csv": str(CATALOG_PRIORITIES_CSV.relative_to(ROOT)),
            "final_chart_staleness_csv": str(FINAL_CHART_STALENESS_CSV.relative_to(ROOT)),
            "play_count_decreases_csv": str(PLAY_COUNT_DECREASES_CSV.relative_to(ROOT)),
            "stale_listing_play_counts_csv": str(STALE_LISTING_COUNTS_CSV.relative_to(ROOT)),
        },
    }
    LOGS.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2))

    top_issues = "\n".join(
        f"- {row['severity'].upper()} {row['area']}/{row['issue_type']}: {row['count']} - {row['recommended_action']}"
        for row in issues[:12]
    )
    top_priorities = "\n".join(
        f"- {row['game_name']} (score {row['priority_score']}, best rank {row['best_rank']}, metrics rows {row['metrics_rows']})"
        for row in priority_rows[:12]
    )
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Kongregate Data Quality Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- As of: {report['as_of']}",
                f"- Ranked rows: {report['ranked_rows']}",
                f"- Ranked rows with play counts: {report['ranked_rows_with_play_counts']}",
                f"- Ranked date range: {report['ranked_date_range'][0]} to {report['ranked_date_range'][1]}",
                f"- Mini catalog games: {report['catalog_games']}",
                f"- Metrics history rows/games: {report['metrics_history_rows']} / {report['metrics_history_games']}",
                f"- Metrics date range: {report['metrics_history_date_range'][0]} to {report['metrics_history_date_range'][1]}",
                f"- Invalid cached HTML files: {report['invalid_cached_html_files']}",
                "",
                "## Top Issues",
                "",
                top_issues or "- No issues detected.",
                "",
                "## Top Metrics Backfill Priorities",
                "",
                top_priorities or "- No priority rows.",
                "",
            ]
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
