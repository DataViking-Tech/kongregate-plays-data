#!/usr/bin/env python3
"""Build the Kongregate mini catalog from games that reached top-N rankings."""

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from kongregate_canonical import canonical_game_url as shared_canonical_game_url


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

RANKED_CSV = PROCESSED / "ranked_games.csv"
CATALOG_CSV = PROCESSED / "mini_catalog.csv"
CATALOG_JSON = PROCESSED / "mini_catalog.json"
REPORT_JSON = LOGS / "mini_catalog_report.json"
REPORT_MD = LOGS / "mini_catalog_report.md"

CATALOG_COLUMNS = [
    "canonical_game_key",
    "game_url",
    "game_url_variants",
    "game_name",
    "developer",
    "first_seen_date",
    "last_seen_date",
    "best_rank",
    "top_n_appearances",
    "ranking_types",
    "categories",
    "first_source_url",
    "first_capture_timestamp",
    "last_source_url",
    "last_capture_timestamp",
    "listing_play_count_rows",
    "max_listing_play_count_observed",
    "needs_game_page_history",
]


def best_counter_value(counter: Counter[str]) -> str:
    if not counter:
        return ""
    return counter.most_common(1)[0][0]


def canonical_game_url(game_url: str) -> str:
    return shared_canonical_game_url(game_url)


def preferred_game_url(counter: Counter[str]) -> str:
    if not counter:
        return ""

    def score(url: str) -> tuple[int, int, int, str]:
        parsed = urllib.parse.urlsplit(url)
        host = parsed.netloc.lower().rstrip(".")
        scheme_score = 1 if parsed.scheme == "https" else 0
        host_score = 1 if host == "www.kongregate.com" else 0
        en_penalty = 1 if parsed.path.startswith("/en/games/") else 0
        return (counter[url], scheme_score, host_score - en_penalty, url)

    return max(counter, key=score)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a catalog of games that reached the top N in captured Kongregate rankings.")
    parser.add_argument("--top-n", type=int, default=20, help="Include games with at least one rank_on_date at or below this number.")
    args = parser.parse_args()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    catalog: dict[str, dict[str, object]] = {}
    input_rows = list(csv.DictReader(RANKED_CSV.open(newline="", encoding="utf-8")))

    for row in input_rows:
        try:
            rank = int(row.get("rank_on_date") or 0)
        except ValueError:
            continue
        game_url = row.get("game_url", "")
        canonical_key = canonical_game_url(game_url)
        if not game_url or not canonical_key or rank <= 0 or rank > args.top_n:
            continue

        item = catalog.setdefault(
            canonical_key,
            {
                "canonical_game_key": canonical_key,
                "game_urls": Counter(),
                "names": Counter(),
                "developers": Counter(),
                "first_seen_date": row["date"],
                "last_seen_date": row["date"],
                "best_rank": rank,
                "top_n_appearances": 0,
                "ranking_types": Counter(),
                "categories": Counter(),
                "first_source_url": row.get("source_url", ""),
                "first_capture_timestamp": row.get("capture_timestamp", ""),
                "last_source_url": row.get("source_url", ""),
                "last_capture_timestamp": row.get("capture_timestamp", ""),
                "listing_play_count_rows": 0,
                "max_listing_play_count_observed": 0,
            },
        )

        item["game_urls"][game_url] += 1
        item["names"][row.get("game_name", "")] += 1
        if row.get("developer"):
            item["developers"][row["developer"]] += 1
        item["best_rank"] = min(int(item["best_rank"]), rank)
        item["top_n_appearances"] = int(item["top_n_appearances"]) + 1
        item["ranking_types"][row.get("ranking_type", "")] += 1
        if row.get("category"):
            item["categories"][row["category"]] += 1
        if row["date"] < item["first_seen_date"]:
            item["first_seen_date"] = row["date"]
            item["first_source_url"] = row.get("source_url", "")
            item["first_capture_timestamp"] = row.get("capture_timestamp", "")
        if row["date"] > item["last_seen_date"]:
            item["last_seen_date"] = row["date"]
            item["last_source_url"] = row.get("source_url", "")
            item["last_capture_timestamp"] = row.get("capture_timestamp", "")
        plays = row.get("plays_count_observed", "")
        if plays:
            try:
                plays_count = int(plays)
            except ValueError:
                plays_count = 0
            item["listing_play_count_rows"] = int(item["listing_play_count_rows"]) + 1
            item["max_listing_play_count_observed"] = max(int(item["max_listing_play_count_observed"]), plays_count)

    rows = []
    for item in catalog.values():
        listing_play_rows = int(item["listing_play_count_rows"])
        game_url_variants = sorted(item["game_urls"])
        rows.append(
            {
                "canonical_game_key": item["canonical_game_key"],
                "game_url": preferred_game_url(item["game_urls"]),
                "game_url_variants": "; ".join(game_url_variants),
                "game_name": best_counter_value(item["names"]),
                "developer": best_counter_value(item["developers"]),
                "first_seen_date": item["first_seen_date"],
                "last_seen_date": item["last_seen_date"],
                "best_rank": item["best_rank"],
                "top_n_appearances": item["top_n_appearances"],
                "ranking_types": "; ".join(key for key, _count in item["ranking_types"].most_common() if key),
                "categories": "; ".join(key for key, _count in item["categories"].most_common() if key),
                "first_source_url": item["first_source_url"],
                "first_capture_timestamp": item["first_capture_timestamp"],
                "last_source_url": item["last_source_url"],
                "last_capture_timestamp": item["last_capture_timestamp"],
                "listing_play_count_rows": listing_play_rows,
                "max_listing_play_count_observed": item["max_listing_play_count_observed"] or "",
                "needs_game_page_history": "yes" if listing_play_rows == 0 else "partial" if listing_play_rows < int(item["top_n_appearances"]) else "no",
            }
        )

    rows.sort(key=lambda row: (int(row["best_rank"]), -int(row["top_n_appearances"]), row["game_name"].lower()))

    with CATALOG_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CATALOG_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    CATALOG_JSON.write_text(json.dumps({"columns": CATALOG_COLUMNS, "top_n": args.top_n, "rows": rows}, indent=2))

    by_status = Counter(row["needs_game_page_history"] for row in rows)
    report = {
        "run_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "top_n": args.top_n,
        "ranked_rows_read": len(input_rows),
        "catalog_games": len(rows),
        "history_status_counts": dict(sorted(by_status.items())),
        "first_seen_date": min((row["first_seen_date"] for row in rows), default=""),
        "last_seen_date": max((row["last_seen_date"] for row in rows), default=""),
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2))
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Kongregate Mini Catalog Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- Top-N threshold: {report['top_n']}",
                f"- Ranked rows read: {report['ranked_rows_read']}",
                f"- Catalog games: {report['catalog_games']}",
                f"- History status counts: {report['history_status_counts']}",
                f"- Date range: {report['first_seen_date']} to {report['last_seen_date']}",
                "",
            ]
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
