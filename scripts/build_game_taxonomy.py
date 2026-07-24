#!/usr/bin/env python3
"""Build an auditable higher-level taxonomy for the Kongregate mini catalog."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"
LIFECYCLE_CSV = PROCESSED / "game_lifecycle_catalog.csv"
OUTPUT_CSV = PROCESSED / "game_taxonomy.csv"
OUTPUT_JSON = PROCESSED / "game_taxonomy.json"
REPORT_JSON = LOGS / "game_taxonomy_report.json"
REPORT_MD = LOGS / "game_taxonomy_report.md"
TAXONOMY_VERSION = "1.0.0"


OUTPUT_COLUMNS = [
    "canonical_game_key",
    "game_name",
    "developer",
    "game_url",
    "best_rank",
    "top_n_appearances",
    "first_observed_date",
    "likely_added_date",
    "observed_categories",
    "primary_genre",
    "genre_tags",
    "genre_confidence",
    "engagement_tags",
    "engagement_confidence",
    "social_platform_status",
    "social_platform_confidence",
    "social_platform_signals",
    "developer_group_key",
    "developer_catalog_game_count",
    "series_group_key",
    "series_catalog_game_count",
    "classification_confidence",
    "classification_signals",
    "review_status",
    "taxonomy_version",
]


# These are Kongregate's observed category slugs, not labels inferred from a title.
CATEGORY_TO_GENRE = {
    "action": "action",
    "adventure": "adventure",
    "adventure-rpg": "role_playing",
    "card": "card_strategy",
    "idle": "idle_incremental",
    "mmo": "role_playing",
    "more": "other",
    "multiplayer": "multiplayer",
    "puzzle": "puzzle",
    "shooter": "shooter",
    "sports-racing": "sports_racing",
    "strategy": "strategy",
    "strategy-defense": "strategy",
    "tower-defense": "tower_defense",
}

PRIMARY_GENRE_PRIORITY = [
    "tower_defense",
    "shooter",
    "puzzle",
    "idle_incremental",
    "sports_racing",
    "card_strategy",
    "role_playing",
    "strategy",
    "adventure",
    "action",
    "multiplayer",
    "other",
]

TITLE_GENRE_RULES = [
    ("idle_incremental", re.compile(r"\b(idle|clicker|incremental|tapper)\b", re.IGNORECASE)),
    ("tower_defense", re.compile(r"\b(tower[ -]?defense)\b", re.IGNORECASE)),
    ("role_playing", re.compile(r"\b(rpg|role[ -]?playing)\b", re.IGNORECASE)),
    ("escape_room", re.compile(r"\b(escape|escape room)\b", re.IGNORECASE)),
    ("sports_racing", re.compile(r"\b(racing|soccer|football|basketball|tennis)\b", re.IGNORECASE)),
]

# A publisher match is a review cue, not a claim that every game was on Facebook.
SOCIAL_PUBLISHER_SIGNALS = {
    "5thplanetgames",
    "edgebee",
    "kanoapps",
    "kixeye",
    "plarium",
    "playmage",
    "r2games",
    "synapticon",
}

TITLE_SOCIAL_RE = re.compile(r"\bfacebook\b", re.IGNORECASE)
TITLE_MMO_RE = re.compile(r"\b(mmo|mmorpg)\b", re.IGNORECASE)
TITLE_MULTIPLAYER_RE = re.compile(r"\bmultiplayer\b", re.IGNORECASE)
SEQUEL_SUFFIX_RE = re.compile(
    r"\b(?:episode|chapter|part|act|season)\s+[0-9ivxlcdm]+\b|\b(?:[0-9]+|[ivxlcdm]+)\b$",
    re.IGNORECASE,
)
PUNCTUATION_RE = re.compile(r"[^a-z0-9]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_int(value: str) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def normalized_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    return PUNCTUATION_RE.sub("-", normalized).strip("-")


def series_stem(name: str) -> str:
    plain = re.sub(r"[\[\(].*?[\]\)]", " ", name)
    plain = SEQUEL_SUFFIX_RE.sub("", plain.strip())
    return normalized_key(plain)


def category_genres(categories: list[str]) -> list[str]:
    return sorted({CATEGORY_TO_GENRE[category] for category in categories if category in CATEGORY_TO_GENRE})


def primary_genre(genres: list[str], title: str) -> tuple[str, str, list[str]]:
    if genres:
        for genre in PRIMARY_GENRE_PRIORITY:
            if genre in genres:
                return genre, "high_observed_category", [f"observed_category:{genre}"]

    for genre, pattern in TITLE_GENRE_RULES:
        if pattern.search(title):
            return genre, "medium_title_signal", [f"title_signal:{genre}"]

    return "unclassified", "none", []


def engagement(categories: list[str], title: str) -> tuple[list[str], str, list[str]]:
    tags: set[str] = set()
    signals: list[str] = []
    if "mmo" in categories:
        tags.add("massively_multiplayer")
        signals.append("observed_category:mmo")
    if "multiplayer" in categories:
        tags.add("online_multiplayer")
        signals.append("observed_category:multiplayer")
    if "card" in categories:
        tags.add("persistent_card_game")
        signals.append("observed_category:card")
    if "idle" in categories:
        tags.add("idle_progression")
        signals.append("observed_category:idle")

    if tags:
        return sorted(tags), "high_observed_category", signals
    if TITLE_MMO_RE.search(title):
        return ["massively_multiplayer_title_signal"], "medium_title_signal", ["title_signal:mmo"]
    if TITLE_MULTIPLAYER_RE.search(title):
        return ["online_multiplayer_title_signal"], "medium_title_signal", ["title_signal:multiplayer"]
    return [], "none", []


def social_platform(developer_key: str, title: str) -> tuple[str, str, list[str]]:
    if developer_key in SOCIAL_PUBLISHER_SIGNALS:
        return "publisher_portfolio_candidate", "medium_curated_publisher", [f"publisher_signal:{developer_key}"]
    if TITLE_SOCIAL_RE.search(title):
        return "title_reference_requires_review", "low_title_signal", ["title_signal:facebook"]
    return "not_assessed", "none", []


def build_rows(lifecycle_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    developer_counts = Counter(normalized_key(row.get("developer", "")) or "unknown" for row in lifecycle_rows)
    series_members: defaultdict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in lifecycle_rows:
        developer_key = normalized_key(row.get("developer", "")) or "unknown"
        stem = series_stem(row.get("game_name", ""))
        if developer_key != "unknown" and len(stem) >= 5 and "-" in stem:
            series_members[(developer_key, stem)].append(row)

    series_counts = {key: len(members) for key, members in series_members.items() if len(members) >= 2}
    rows: list[dict[str, object]] = []

    for lifecycle in lifecycle_rows:
        categories = split_semicolon(lifecycle.get("observed_categories", ""))
        title = lifecycle.get("game_name", "")
        developer_key = normalized_key(lifecycle.get("developer", "")) or "unknown"
        genres = category_genres(categories)
        primary, genre_confidence, genre_signals = primary_genre(genres, title)
        if primary != "unclassified" and primary not in genres:
            genres.append(primary)
            genres.sort()
        engagement_tags, engagement_confidence, engagement_signals = engagement(categories, title)
        social_status, social_confidence, social_signals = social_platform(developer_key, title)

        stem = series_stem(title)
        series_count = series_counts.get((developer_key, stem), 0)
        series_key = f"{developer_key}:{stem}" if series_count else ""
        signals = genre_signals + engagement_signals + social_signals
        if series_key:
            signals.append("same_developer_series_stem")

        confidences = {genre_confidence, engagement_confidence, social_confidence}
        if "high_observed_category" in confidences:
            overall_confidence = "high"
        elif "medium_title_signal" in confidences or "medium_curated_publisher" in confidences:
            overall_confidence = "medium"
        else:
            overall_confidence = "low" if signals else "none"

        review_status = "ready"
        if social_status != "not_assessed":
            review_status = "review_social_platform"
        elif genre_confidence == "medium_title_signal" or engagement_confidence == "medium_title_signal":
            review_status = "review_title_inference"

        rows.append(
            {
                "canonical_game_key": lifecycle.get("canonical_game_key", ""),
                "game_name": title,
                "developer": lifecycle.get("developer", ""),
                "game_url": lifecycle.get("game_url", ""),
                "best_rank": parse_int(lifecycle.get("best_rank", "")),
                "top_n_appearances": parse_int(lifecycle.get("top_n_appearances", "")),
                "first_observed_date": lifecycle.get("first_observed_date", ""),
                "likely_added_date": lifecycle.get("likely_added_date", ""),
                "observed_categories": "; ".join(categories),
                "primary_genre": primary,
                "genre_tags": "; ".join(genres),
                "genre_confidence": genre_confidence,
                "engagement_tags": "; ".join(engagement_tags),
                "engagement_confidence": engagement_confidence,
                "social_platform_status": social_status,
                "social_platform_confidence": social_confidence,
                "social_platform_signals": "; ".join(social_signals),
                "developer_group_key": developer_key,
                "developer_catalog_game_count": developer_counts[developer_key],
                "series_group_key": series_key,
                "series_catalog_game_count": series_count,
                "classification_confidence": overall_confidence,
                "classification_signals": "; ".join(signals),
                "review_status": review_status,
                "taxonomy_version": TAXONOMY_VERSION,
            }
        )

    rows.sort(key=lambda row: (int(row["best_rank"] or 9999), -int(row["top_n_appearances"] or 0), str(row["game_name"]).lower()))
    return rows


def write_outputs(rows: list[dict[str, object]]) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    OUTPUT_JSON.write_text(json.dumps({"columns": OUTPUT_COLUMNS, "rows": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def report(rows: list[dict[str, object]]) -> dict[str, object]:
    counts = lambda field: dict(sorted(Counter(str(row.get(field, "")) or "blank" for row in rows).items()))
    social_candidates = sorted(
        (row for row in rows if row["social_platform_status"] != "not_assessed"),
        key=lambda row: (int(row["best_rank"] or 9999), -int(row["top_n_appearances"] or 0), str(row["game_name"]).lower()),
    )
    return {
        "generated_at": utc_now(),
        "taxonomy_version": TAXONOMY_VERSION,
        "catalog_games": len(rows),
        "primary_genre_counts": counts("primary_genre"),
        "genre_confidence_counts": counts("genre_confidence"),
        "engagement_tag_counts": dict(
            sorted(Counter(tag for row in rows for tag in split_semicolon(str(row.get("engagement_tags", "")))).items())
        ),
        "social_platform_status_counts": counts("social_platform_status"),
        "review_status_counts": counts("review_status"),
        "developer_groups_with_multiple_games": sum(1 for row in rows if int(row["developer_catalog_game_count"]) >= 2),
        "same_developer_series_groups": len({row["series_group_key"] for row in rows if row["series_group_key"]}),
        "social_platform_review_candidates": [
            {
                "game_name": row["game_name"],
                "developer": row["developer"],
                "best_rank": row["best_rank"],
                "status": row["social_platform_status"],
                "signals": row["social_platform_signals"],
            }
            for row in social_candidates
        ],
        "outputs": {
            "csv": str(OUTPUT_CSV.relative_to(ROOT)),
            "json": str(OUTPUT_JSON.relative_to(ROOT)),
            "report_json": str(REPORT_JSON.relative_to(ROOT)),
            "report_md": str(REPORT_MD.relative_to(ROOT)),
        },
    }


def write_report(payload: dict[str, object]) -> None:
    social_lines = [
        f"- {candidate['game_name']} ({candidate['developer'] or 'unknown developer'}, best rank {candidate['best_rank']}): {candidate['status']} [{candidate['signals']}]"
        for candidate in payload["social_platform_review_candidates"]
    ]
    REPORT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Kongregate Game Taxonomy Report",
                "",
                f"- Generated at: {payload['generated_at']}",
                f"- Taxonomy version: {payload['taxonomy_version']}",
                f"- Catalog games: {payload['catalog_games']}",
                f"- Primary genres: {payload['primary_genre_counts']}",
                f"- Engagement tags: {payload['engagement_tag_counts']}",
                f"- Social-platform review states: {payload['social_platform_status_counts']}",
                f"- Review states: {payload['review_status_counts']}",
                f"- Developer groups with multiple catalog games: {payload['developer_groups_with_multiple_games']}",
                f"- Same-developer series groups: {payload['same_developer_series_groups']}",
                "",
                "## Interpretation",
                "",
                "- High-confidence genre and engagement labels come from observed Kongregate category pages.",
                "- Title and publisher signals are separated from direct category evidence and marked for review.",
                "- A social-platform candidate is not a claim that a game was published on Facebook; it is a queue for source-backed verification.",
                "",
                "## Social-Platform Review Queue",
                "",
                *social_lines,
                "",
                "## Outputs",
                "",
                f"- `{payload['outputs']['csv']}`",
                f"- `{payload['outputs']['json']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    rows = build_rows(read_csv(LIFECYCLE_CSV))
    payload = report(rows)
    write_outputs(rows)
    write_report(payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
