#!/usr/bin/env python3
"""Build evidence-backed lifecycle and provisional category metadata."""

from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from kongregate_canonical import canonical_game_url


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"
RAW_METRICS = ROOT / "data" / "raw" / "game_metrics"
RAW_HTML = ROOT / "data" / "raw" / "html"
RAW_GAME_PAGES = ROOT / "data" / "raw" / "game_pages"

MINI_CATALOG_CSV = PROCESSED / "mini_catalog.csv"
RANKED_CSV = PROCESSED / "ranked_games.csv"
HISTORY_CSV = PROCESSED / "game_play_history.csv"
AUDIT_CSV = PROCESSED / "metrics_backfill_gap_audit.csv"
PAGE_GAP_CSV = PROCESSED / "game_page_gap_progress.csv"
COUNT_SOURCE_STATUS_CSV = PROCESSED / "count_source_probe_game_status.csv"
LIVE_MANIFEST_JSON = RAW_METRICS / "live_manifest.json"
LIVE_FAILURES_JSON = RAW_METRICS / "live_failures.json"
LIVE_PAGE_STATUS_JSON = RAW_GAME_PAGES / "live_page_status.json"

OUTPUT_CSV = PROCESSED / "game_lifecycle_catalog.csv"
OUTPUT_JSON = PROCESSED / "game_lifecycle_catalog.json"
REPORT_JSON = LOGS / "game_lifecycle_catalog_report.json"
REPORT_MD = LOGS / "game_lifecycle_catalog_report.md"

DATE_COLUMNS = {
    "first_observed_date",
    "first_ranked_date",
    "first_play_history_date",
    "first_live_metric_date",
    "published_date",
    "likely_added_date",
    "last_observed_date",
    "last_ranked_date",
    "last_play_history_date",
    "last_live_metric_date",
    "latest_live_metric_attempt_date",
    "latest_live_page_attempt_date",
    "observed_removed_after_date",
    "observed_removed_by_date",
}

OUTPUT_COLUMNS = [
    "canonical_game_key",
    "game_name",
    "developer",
    "game_url",
    "kongregate_game_ids",
    "best_rank",
    "top_n_appearances",
    "ranking_types",
    "observed_categories",
    "category_tags",
    "platform_flags",
    "facebook_social_candidate",
    "classification_confidence",
    "classification_signals",
    "first_observed_date",
    "first_observed_source",
    "first_ranked_date",
    "first_play_history_date",
    "first_live_metric_date",
    "published_date",
    "published_date_source",
    "published_date_confidence",
    "likely_added_date",
    "likely_added_date_confidence",
    "last_observed_date",
    "last_observed_source",
    "last_ranked_date",
    "last_play_history_date",
    "last_live_metric_date",
    "current_live_metric_status",
    "latest_live_metric_attempt_date",
    "current_live_page_status",
    "latest_live_page_attempt_date",
    "removal_evidence_status",
    "removal_evidence_type",
    "observed_removed_after_date",
    "observed_removed_by_date",
    "removal_confidence",
    "metrics_rows",
    "listing_play_count_rows",
    "max_play_count_observed",
    "page_gap_status",
    "metrics_audit_status",
    "count_source_probe_status",
    "notes",
]

SOCIAL_PUBLISHER_HINTS = {
    "5thplanetgames",
    "amzgame",
    "edgebee",
    "frozenshardgames",
    "plarium",
    "playmage",
    "r2games",
    "synapticon",
}

SOCIAL_TITLE_RE = re.compile(
    r"\b("
    r"facebook|social|guild|alliance|empire|kingdom|tyrant|dragon|dragons|"
    r"mafia|war|wars|battle|battles|clan|clans"
    r")\b",
    re.IGNORECASE,
)

GENRE_RULES = [
    ("idle_clicker", re.compile(r"\b(idle|clicker|incremental|tap|tapper)\b", re.IGNORECASE)),
    ("tower_defense", re.compile(r"\b(tower defense|tower-defense|\btd\b)\b", re.IGNORECASE)),
    ("mmo_multiplayer", re.compile(r"\b(mmo|mmorpg|multiplayer|arena|guild|clan|alliance)\b", re.IGNORECASE)),
    ("card_battler", re.compile(r"\b(card|cards|deck|tyrant)\b", re.IGNORECASE)),
    ("escape_room", re.compile(r"\b(escape|room escape|hidden)\b", re.IGNORECASE)),
    ("racing_sports", re.compile(r"\b(racing|race|football|soccer|sports|tennis|basketball)\b", re.IGNORECASE)),
]

GAME_URL_RE = re.compile(r"https?://www\.kongregate\.com/(?:en/)?games/[^\"'<>\s?#]+/[^\"'<>\s?#&]+", re.IGNORECASE)
DATE_RE = re.compile(r"\b(20\d{2}|19\d{2})-(\d{2})-(\d{2})(?!\d)")
JSON_LD_RE = re.compile(
    r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
PUBLISHED_TEXT_RE = re.compile(
    r"Game\s+(published|uploaded)\s+on\s+(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)
PUBLISHED_BLOCK_RE = re.compile(
    r"<div[^>]+id=[\"']game_published[\"'][^>]*>.*?(\d{4}-\d{2}-\d{2}).*?</div>",
    re.IGNORECASE | re.DOTALL,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def parse_int(value) -> int:
    if value in (None, ""):
        return 0
    match = re.search(r"\d[\d,]*", str(value))
    return int(match.group(0).replace(",", "")) if match else 0


def date_from_timestamp(timestamp: str) -> str:
    if not timestamp or len(timestamp) < 8:
        return ""
    try:
        return datetime.strptime(timestamp[:8], "%Y%m%d").date().isoformat()
    except ValueError:
        return ""


def iso_date_from_timestamp(value: str) -> str:
    if not value:
        return ""
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", value)
    if match:
        return match.group(1)
    return date_from_timestamp(value)


def normalize_iso_date(value: str) -> str:
    match = DATE_RE.search(value or "")
    if not match:
        return ""
    candidate = "-".join(match.groups())
    try:
        parsed = datetime.strptime(candidate, "%Y-%m-%d").date()
    except ValueError:
        return ""
    if parsed.isoformat() < "2006-01-01" or parsed.isoformat() > datetime.now(timezone.utc).date().isoformat():
        return ""
    return parsed.isoformat()


def split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";") if part.strip()]


def min_date(values: list[str]) -> str:
    dates = sorted(value for value in values if value)
    return dates[0] if dates else ""


def max_date(values: list[str]) -> str:
    dates = sorted(value for value in values if value)
    return dates[-1] if dates else ""


def append_source_date(bucket: dict[str, list[str]], source: str, date: str) -> None:
    if date:
        bucket[source].append(date)


def source_for_date(source_dates: dict[str, list[str]], target_date: str, first: bool) -> str:
    if not target_date:
        return ""
    matches = sorted(source for source, dates in source_dates.items() if target_date in dates)
    if matches:
        return "; ".join(matches)
    all_sources = [(date, source) for source, dates in source_dates.items() for date in dates]
    if not all_sources:
        return ""
    return sorted(all_sources)[0 if first else -1][1]


def build_lookup(rows: list[dict[str, str]], status_field: str = "status") -> dict[str, dict[str, str]]:
    lookup = {}
    for row in rows:
        key = canonical_game_url(row.get("game_url", ""))
        if key:
            lookup[key] = row
    return lookup


def is_video_game_node(node: dict) -> bool:
    node_type = node.get("@type")
    if isinstance(node_type, list):
        return any(str(value).lower() == "videogame" for value in node_type)
    return str(node_type).lower() == "videogame"


def iter_json_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_json_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_json_nodes(child)


def extract_json_ld_documents(markup: str) -> list:
    documents = []
    for match in JSON_LD_RE.finditer(markup):
        payload = html.unescape(match.group(1)).strip()
        if not payload:
            continue
        try:
            documents.append(json.loads(payload))
        except json.JSONDecodeError:
            continue
    return documents


def extract_structured_published_dates(markup: str) -> list[tuple[str, str]]:
    found = []
    for document in extract_json_ld_documents(markup):
        for node in iter_json_nodes(document):
            if not is_video_game_node(node):
                continue
            game_url = node.get("url") or node.get("@id", "")
            published_date = normalize_iso_date(str(node.get("datePublished", "")))
            key = canonical_game_url(str(game_url))
            if key and published_date:
                found.append((key, published_date))
    return found


def extract_page_game_url(markup: str) -> str:
    meta_patterns = [
        r"<meta[^>]+property=[\"']og:url[\"'][^>]+content=[\"']([^\"']+)[\"']",
        r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']+)[\"']",
        r"<link[^>]+href=[\"']([^\"']+)[\"'][^>]+rel=[\"']canonical[\"']",
    ]
    for pattern in meta_patterns:
        match = re.search(pattern, markup, re.IGNORECASE)
        if match:
            key = canonical_game_url(html.unescape(match.group(1)))
            if key:
                return key

    game_url_match = re.search(r"[\"']game_url[\"']\s*:\s*[\"']([^\"']+)[\"']", markup, re.IGNORECASE)
    if game_url_match:
        from urllib.parse import unquote

        key = canonical_game_url(unquote(game_url_match.group(1)))
        if key:
            return key

    candidates = Counter(canonical_game_url(html.unescape(match.group(0))) for match in GAME_URL_RE.finditer(markup))
    candidates = Counter({key: count for key, count in candidates.items() if key})
    if candidates:
        return candidates.most_common(1)[0][0]
    return ""


def add_published_evidence(
    evidence: dict[str, dict[str, object]],
    key: str,
    published_date: str,
    source_type: str,
    path: Path,
) -> None:
    if not key or not published_date:
        return
    bucket = evidence[key]
    bucket["dates"][published_date] += 1
    bucket["source_types"][source_type] += 1
    if len(bucket["sample_paths"]) < 5:
        bucket["sample_paths"].add(str(path.relative_to(ROOT)))


def collect_published_dates() -> dict[str, dict[str, object]]:
    evidence: dict[str, dict[str, object]] = defaultdict(lambda: {
        "dates": Counter(),
        "source_types": Counter(),
        "sample_paths": set(),
    })
    html_roots = [RAW_GAME_PAGES / "html", RAW_GAME_PAGES / "probe", RAW_HTML]
    for html_root in html_roots:
        if not html_root.exists():
            continue
        for path in sorted(html_root.glob("*.html")):
            markup = path.read_text(encoding="utf-8", errors="replace")

            for key, published_date in extract_structured_published_dates(markup):
                add_published_evidence(evidence, key, published_date, "json_ld_datePublished", path)

            page_key = extract_page_game_url(markup)
            if not page_key:
                continue
            for match in PUBLISHED_TEXT_RE.finditer(markup):
                source_type = f"html_game_{match.group(1).lower()}_text"
                add_published_evidence(evidence, page_key, normalize_iso_date(match.group(2)), source_type, path)
            for match in PUBLISHED_BLOCK_RE.finditer(markup):
                add_published_evidence(evidence, page_key, normalize_iso_date(match.group(1)), "html_game_published_block", path)
    return evidence


def choose_published_date(evidence: dict[str, object] | None) -> tuple[str, str, str]:
    if not evidence:
        return "", "", ""
    dates: Counter = evidence.get("dates", Counter())
    if not dates:
        return "", "", ""
    max_count = max(dates.values())
    published_date = sorted(date for date, count in dates.items() if count == max_count)[0]
    source_types: Counter = evidence.get("source_types", Counter())
    source = "; ".join(f"{source}:{count}" for source, count in sorted(source_types.items()))
    confidence = "published_date_from_archived_game_page"
    if source_types and set(source_types) == {"json_ld_datePublished"}:
        confidence = "published_date_from_structured_json_ld"
    return published_date, source, confidence


def load_live_page_statuses() -> dict[str, dict[str, str]]:
    statuses = read_json(LIVE_PAGE_STATUS_JSON, {})
    return {key: row for key, row in statuses.items() if key}


def live_page_unavailable(status: str) -> bool:
    return status.startswith("live_page_http_") or status == "live_page_unavailable_text"


def collect_observations() -> tuple[dict[str, dict[str, object]], dict[str, dict[str, str]]]:
    observations: dict[str, dict[str, object]] = defaultdict(lambda: {
        "ranked_dates": [],
        "history_dates": [],
        "live_dates": [],
        "source_dates": defaultdict(list),
        "max_play_count": 0,
        "history_rows": 0,
    })

    for row in read_csv(RANKED_CSV):
        key = canonical_game_url(row.get("game_url", ""))
        date = row.get("date", "")
        if not key or not date:
            continue
        obs = observations[key]
        obs["ranked_dates"].append(date)
        append_source_date(obs["source_dates"], "ranked_list", date)
        obs["max_play_count"] = max(obs["max_play_count"], parse_int(row.get("plays_count_observed")))

    for row in read_csv(HISTORY_CSV):
        key = canonical_game_url(row.get("game_url", ""))
        date = row.get("date", "")
        if not key or not date:
            continue
        obs = observations[key]
        obs["history_dates"].append(date)
        obs["history_rows"] += 1
        parser = row.get("parser", "") or "game_play_history"
        append_source_date(obs["source_dates"], parser, date)
        obs["max_play_count"] = max(obs["max_play_count"], parse_int(row.get("plays_count_observed")))

    live_by_key: dict[str, dict[str, str]] = {}
    for _path, meta in read_json(LIVE_MANIFEST_JSON, {}).items():
        key = canonical_game_url(meta.get("game_url", ""))
        date = date_from_timestamp(meta.get("capture_timestamp", ""))
        if not key or not date:
            continue
        obs = observations[key]
        obs["live_dates"].append(date)
        append_source_date(obs["source_dates"], "live_metrics_json", date)
        live_by_key[key] = {
            "status": "live_metrics_available",
            "date": date,
            "attempt_date": date,
            "error": "",
        }

    for _key, failure in read_json(LIVE_FAILURES_JSON, {}).items():
        key = canonical_game_url(failure.get("game_url", ""))
        if not key or key in live_by_key:
            continue
        error = failure.get("last_error", "")
        attempt_date = iso_date_from_timestamp(failure.get("last_attempt_timestamp", ""))
        status = f"live_metrics_failed_{error}" if error else "live_metrics_failed"
        live_by_key[key] = {
            "status": status,
            "date": "",
            "attempt_date": attempt_date,
            "error": error,
        }

    return observations, live_by_key


def classify_game(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    categories = split_semicolon(row.get("categories", ""))
    ranking_types = split_semicolon(row.get("ranking_types", ""))
    text = " ".join(
        [
            row.get("game_name", ""),
            row.get("developer", ""),
            row.get("game_url", ""),
            row.get("categories", ""),
            row.get("ranking_types", ""),
        ]
    )
    tags = set(categories)
    flags = set()
    signals = []

    for tag, pattern in GENRE_RULES:
        if pattern.search(text):
            tags.add(tag)
            signals.append(f"name_or_category:{tag}")

    if "mmo" in categories or "multiplayer" in categories:
        flags.add("networked_social_play")
        signals.append("category:mmo_or_multiplayer")
    if "card" in categories:
        flags.add("persistent_card_meta")
        signals.append("category:card")
    if "idle" in categories:
        flags.add("persistent_progression")
        signals.append("category:idle")
    if "most_played" in ranking_types:
        flags.add("most_played_ranked")

    developer_key = row.get("developer", "").lower()
    social_score = 0
    if developer_key in SOCIAL_PUBLISHER_HINTS:
        social_score += 2
        signals.append(f"publisher_hint:{developer_key}")
    if SOCIAL_TITLE_RE.search(text):
        social_score += 1
        signals.append("title_or_slug_social_strategy_terms")
    if {"mmo", "multiplayer", "card"} & set(categories):
        social_score += 1
        signals.append("category_social_candidate")

    if social_score >= 3:
        candidate = "likely"
        confidence = "medium"
        flags.add("facebook_or_social_platform_candidate")
    elif social_score >= 2:
        candidate = "possible"
        confidence = "low"
        flags.add("social_platform_candidate")
    else:
        candidate = "no"
        confidence = "low" if signals else ""

    return (
        "; ".join(sorted(tags)),
        "; ".join(sorted(flags)),
        candidate,
        confidence,
        "; ".join(dict.fromkeys(signals)),
    )


def lifecycle_row(
    catalog_row: dict[str, str],
    observations: dict[str, dict[str, object]],
    live_by_key: dict[str, dict[str, str]],
    live_page_by_key: dict[str, dict[str, str]],
    published_by_key: dict[str, dict[str, object]],
    audit_by_key: dict[str, dict[str, str]],
    page_gap_by_key: dict[str, dict[str, str]],
    count_source_by_key: dict[str, dict[str, str]],
) -> dict[str, object]:
    key = catalog_row.get("canonical_game_key") or canonical_game_url(catalog_row.get("game_url", ""))
    obs = observations.get(key, {})
    ranked_dates = list(obs.get("ranked_dates", []))
    history_dates = list(obs.get("history_dates", []))
    live_dates = list(obs.get("live_dates", []))
    source_dates = obs.get("source_dates", defaultdict(list))
    live = live_by_key.get(key, {"status": "not_checked", "date": "", "attempt_date": "", "error": ""})

    first_ranked = min_date(ranked_dates) or catalog_row.get("first_seen_date", "")
    last_ranked = max_date(ranked_dates) or catalog_row.get("last_seen_date", "")
    first_history = min_date(history_dates)
    last_history = max_date(history_dates)
    first_live = min_date(live_dates)
    last_live = max_date(live_dates)
    first_observed = min_date([first_ranked, first_history, first_live])
    last_observed = max_date([last_ranked, last_history, last_live])
    published_date, published_source, published_confidence = choose_published_date(published_by_key.get(key))
    live_page = live_page_by_key.get(key, {})
    live_page_status = live_page.get("status", "not_checked")
    live_page_attempt_date = iso_date_from_timestamp(live_page.get("last_attempt_timestamp", ""))

    removal_status = "no_removal_evidence"
    removal_type = ""
    removed_after = ""
    removed_by = ""
    removal_confidence = ""
    if live_page_status == "live_page_available":
        removal_status = "live_page_available"
        removal_confidence = "high_page_available"
    elif live_page_unavailable(live_page_status):
        if live_page_attempt_date and last_observed and live_page_attempt_date < last_observed:
            removal_status = "stale_live_page_failure_older_than_last_observation"
            removal_type = live_page_status
            removal_confidence = "not_removal_evidence"
        else:
            removal_status = "live_page_unavailable"
            removal_type = live_page_status
            removed_after = last_observed
            removed_by = live_page_attempt_date
            removal_confidence = "high_live_page_unavailable" if live_page_status.startswith("live_page_http_") else "medium_live_page_unavailable_text"
    elif live.get("status") == "live_metrics_available":
        removal_status = "live_metrics_available"
        removal_confidence = "high_for_metrics_endpoint"
    elif live.get("status", "").startswith("live_metrics_failed"):
        attempt_date = live.get("attempt_date", "")
        if attempt_date and last_observed and attempt_date < last_observed:
            removal_status = "stale_live_metrics_failure_older_than_last_observation"
            removal_type = live.get("error", "")
            removal_confidence = "not_removal_evidence"
        else:
            removal_status = "live_metrics_unavailable"
            removal_type = live.get("error", "")
            removed_after = last_observed
            removed_by = attempt_date
            removal_confidence = "low_game_page_not_verified"

    published_conflicts_with_first_observed = bool(published_date and first_observed and published_date > first_observed)
    likely_added_date = first_observed if published_conflicts_with_first_observed else (published_date or first_observed)
    added_confidence = published_confidence or "observed_first_seen_not_launch_date"
    if published_conflicts_with_first_observed:
        added_confidence = "published_date_after_first_observed_conflict"
    elif not published_date and first_observed <= "2007-01-20":
        added_confidence = "left_censored_at_first_archive_capture"

    category_tags, platform_flags, social_candidate, class_confidence, signals = classify_game(catalog_row)
    notes = []
    if live_page_status == "live_page_available" and live.get("status", "").startswith("live_metrics_failed"):
        notes.append("Live game page is available even though the metrics endpoint failed.")
    if live_page_unavailable(live_page_status):
        notes.append("Live game page availability check is direct page-level removal evidence.")
    if removal_status == "live_metrics_unavailable":
        notes.append("Live metrics endpoint failure is removal evidence only for the metrics endpoint; game-page availability needs direct verification.")
    if published_conflicts_with_first_observed:
        notes.append("Published metadata is after an observed ranking/history date, so likely added date uses the earlier observation.")
    elif published_date:
        notes.append("Likely added date is backed by archived published/uploaded metadata.")
    elif first_observed:
        notes.append("Likely added date is the first observed archive/listing/history date, not a confirmed launch date.")

    return {
        "canonical_game_key": key,
        "game_name": catalog_row.get("game_name", ""),
        "developer": catalog_row.get("developer", ""),
        "game_url": catalog_row.get("game_url", ""),
        "kongregate_game_ids": catalog_row.get("kongregate_game_ids", ""),
        "best_rank": parse_int(catalog_row.get("best_rank")),
        "top_n_appearances": parse_int(catalog_row.get("top_n_appearances")),
        "ranking_types": catalog_row.get("ranking_types", ""),
        "observed_categories": catalog_row.get("categories", ""),
        "category_tags": category_tags,
        "platform_flags": platform_flags,
        "facebook_social_candidate": social_candidate,
        "classification_confidence": class_confidence,
        "classification_signals": signals,
        "first_observed_date": first_observed,
        "first_observed_source": source_for_date(source_dates, first_observed, first=True),
        "first_ranked_date": first_ranked,
        "first_play_history_date": first_history,
        "first_live_metric_date": first_live,
        "published_date": published_date,
        "published_date_source": published_source,
        "published_date_confidence": published_confidence,
        "likely_added_date": likely_added_date,
        "likely_added_date_confidence": added_confidence,
        "last_observed_date": last_observed,
        "last_observed_source": source_for_date(source_dates, last_observed, first=False),
        "last_ranked_date": last_ranked,
        "last_play_history_date": last_history,
        "last_live_metric_date": last_live,
        "current_live_metric_status": live.get("status", "not_checked"),
        "latest_live_metric_attempt_date": live.get("attempt_date", ""),
        "current_live_page_status": live_page_status,
        "latest_live_page_attempt_date": live_page_attempt_date,
        "removal_evidence_status": removal_status,
        "removal_evidence_type": removal_type,
        "observed_removed_after_date": removed_after,
        "observed_removed_by_date": removed_by,
        "removal_confidence": removal_confidence,
        "metrics_rows": obs.get("history_rows", 0),
        "listing_play_count_rows": parse_int(catalog_row.get("listing_play_count_rows")),
        "max_play_count_observed": max(parse_int(catalog_row.get("max_listing_play_count_observed")), obs.get("max_play_count", 0)),
        "page_gap_status": page_gap_by_key.get(key, {}).get("status", ""),
        "metrics_audit_status": audit_by_key.get(key, {}).get("status", ""),
        "count_source_probe_status": count_source_by_key.get(key, {}).get("status", ""),
        "notes": " ".join(notes),
    }


def write_outputs(rows: list[dict[str, object]]) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    OUTPUT_JSON.write_text(json.dumps({"columns": OUTPUT_COLUMNS, "rows": rows}, indent=2))


def main() -> None:
    catalog_rows = read_csv(MINI_CATALOG_CSV)
    observations, live_by_key = collect_observations()
    live_page_by_key = load_live_page_statuses()
    published_by_key = collect_published_dates()
    audit_by_key = build_lookup(read_csv(AUDIT_CSV))
    page_gap_by_key = build_lookup(read_csv(PAGE_GAP_CSV))
    count_source_by_key = build_lookup(read_csv(COUNT_SOURCE_STATUS_CSV))

    rows = [
        lifecycle_row(row, observations, live_by_key, live_page_by_key, published_by_key, audit_by_key, page_gap_by_key, count_source_by_key)
        for row in catalog_rows
    ]
    rows.sort(key=lambda row: (int(row.get("best_rank") or 9999), -int(row.get("top_n_appearances") or 0), row.get("game_name", "").lower()))
    write_outputs(rows)

    social_counts = Counter(row["facebook_social_candidate"] for row in rows)
    live_counts = Counter(row["current_live_metric_status"] for row in rows)
    live_page_counts = Counter(row["current_live_page_status"] for row in rows)
    removal_counts = Counter(row["removal_evidence_status"] for row in rows)
    confidence_counts = Counter(row["classification_confidence"] for row in rows if row["classification_confidence"])
    published_confidence_counts = Counter(row["published_date_confidence"] for row in rows if row["published_date_confidence"])
    likely_added_confidence_counts = Counter(row["likely_added_date_confidence"] for row in rows if row["likely_added_date_confidence"])
    report = {
        "generated_at": utc_now(),
        "catalog_games": len(rows),
        "rows_with_observed_categories": sum(1 for row in rows if row["observed_categories"]),
        "rows_with_published_dates": sum(1 for row in rows if row["published_date"]),
        "published_date_after_first_observed_conflicts": sum(
            1
            for row in rows
            if row["published_date"] and row["first_observed_date"] and row["published_date"] > row["first_observed_date"]
        ),
        "published_date_confidence_counts": dict(sorted(published_confidence_counts.items())),
        "likely_added_date_confidence_counts": dict(sorted(likely_added_confidence_counts.items())),
        "facebook_social_candidate_counts": dict(sorted(social_counts.items())),
        "classification_confidence_counts": dict(sorted(confidence_counts.items())),
        "live_metric_status_counts": dict(sorted(live_counts.items())),
        "live_page_status_counts": dict(sorted(live_page_counts.items())),
        "removal_evidence_status_counts": dict(sorted(removal_counts.items())),
        "first_observed_date_range": [
            min_date([str(row["first_observed_date"]) for row in rows]),
            max_date([str(row["first_observed_date"]) for row in rows]),
        ],
        "published_date_range": [
            min_date([str(row["published_date"]) for row in rows]),
            max_date([str(row["published_date"]) for row in rows]),
        ],
        "likely_added_date_range": [
            min_date([str(row["likely_added_date"]) for row in rows]),
            max_date([str(row["likely_added_date"]) for row in rows]),
        ],
        "last_observed_date_range": [
            min_date([str(row["last_observed_date"]) for row in rows]),
            max_date([str(row["last_observed_date"]) for row in rows]),
        ],
        "top_social_candidates": [
            {
                "game_name": row["game_name"],
                "developer": row["developer"],
                "best_rank": row["best_rank"],
                "candidate": row["facebook_social_candidate"],
                "signals": row["classification_signals"],
            }
            for row in rows
            if row["facebook_social_candidate"] in {"likely", "possible"}
        ][:25],
        "outputs": {
            "csv": str(OUTPUT_CSV.relative_to(ROOT)),
            "json": str(OUTPUT_JSON.relative_to(ROOT)),
            "report_json": str(REPORT_JSON.relative_to(ROOT)),
            "report_md": str(REPORT_MD.relative_to(ROOT)),
        },
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True))
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Kongregate Game Lifecycle Catalog Report",
                "",
                f"- Generated at: {report['generated_at']}",
                f"- Catalog games: {report['catalog_games']}",
                f"- Rows with observed categories: {report['rows_with_observed_categories']}",
                f"- Rows with archived published/uploaded dates: {report['rows_with_published_dates']}",
                f"- Published dates after first observed date: {report['published_date_after_first_observed_conflicts']}",
                f"- Published date confidence counts: {report['published_date_confidence_counts']}",
                f"- Likely added date confidence counts: {report['likely_added_date_confidence_counts']}",
                f"- Facebook/social candidate counts: {report['facebook_social_candidate_counts']}",
                f"- Classification confidence counts: {report['classification_confidence_counts']}",
                f"- Live metric status counts: {report['live_metric_status_counts']}",
                f"- Live page status counts: {report['live_page_status_counts']}",
                f"- Removal evidence status counts: {report['removal_evidence_status_counts']}",
                f"- First observed date range: {report['first_observed_date_range'][0]} to {report['first_observed_date_range'][1]}",
                f"- Published date range: {report['published_date_range'][0]} to {report['published_date_range'][1]}",
                f"- Likely added date range: {report['likely_added_date_range'][0]} to {report['likely_added_date_range'][1]}",
                f"- Last observed date range: {report['last_observed_date_range'][0]} to {report['last_observed_date_range'][1]}",
                "",
                "## Outputs",
                "",
                f"- `{report['outputs']['csv']}`",
                f"- `{report['outputs']['json']}`",
                "",
            ]
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
