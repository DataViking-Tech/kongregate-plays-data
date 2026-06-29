#!/usr/bin/env python3
"""Pilot Wayback reconnaissance for Kongregate ranking-source mapping."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_CDX = ROOT / "data" / "raw" / "cdx"
RAW_HTML = ROOT / "data" / "raw" / "html"
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

CDX_ENDPOINT = "https://web.archive.org/cdx"
WAYBACK_RAW = "https://web.archive.org/web/{timestamp}id_/{original}"
WAYBACK_VIEW = "https://web.archive.org/web/{timestamp}/{original}"

FIELDS = ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]

SEED_URLS = [
    ("home", "https://www.kongregate.com/"),
    ("games", "https://www.kongregate.com/games"),
    ("games_sort_rating", "https://www.kongregate.com/games?sort=rating"),
    ("games_sort_plays", "https://www.kongregate.com/games?sort=plays"),
    ("games_sort_newest", "https://www.kongregate.com/games?sort=newest"),
    ("games_sort_oldest", "https://www.kongregate.com/games?sort=oldest"),
    ("top_rated_games", "https://www.kongregate.com/top-rated-games"),
    ("most_played_games", "https://www.kongregate.com/most-played-games"),
    ("new_games", "https://www.kongregate.com/new-games"),
    ("hot_games", "https://www.kongregate.com/hot-games"),
    ("best_games", "https://www.kongregate.com/best-games"),
]

GENRES = [
    "action",
    "adventure",
    "arcade",
    "puzzle",
    "strategy",
    "sports",
    "multiplayer",
    "shooter",
    "idle",
    "rpg",
    "mmo",
    "defense",
    "platform",
    "music",
    "rhythm",
    "card",
    "board",
    "racing",
    "tower-defense",
    "escape",
    "upgrades",
    "physics",
    "zombie",
    "fantasy",
    "sci-fi",
    "funny",
    "horror",
]

PILOT_GENRES = ["action", "puzzle", "strategy", "shooter", "idle", "tower-defense"]


TAB_COLUMNS = {
    "url_patterns": [
        "pattern_id",
        "pattern_template",
        "example_url",
        "first_seen_timestamp",
        "last_seen_timestamp",
        "status",
        "pattern_type",
        "sort_param",
        "category_param",
        "pagination_style",
        "locale_style",
        "evidence_capture_url",
        "confidence",
        "notes",
    ],
    "capture_coverage": [
        "pattern_id",
        "original_url",
        "year",
        "month",
        "week_start",
        "capture_count",
        "usable_html_count",
        "first_capture_timestamp",
        "last_capture_timestamp",
        "sample_capture_url",
        "status_codes_seen",
        "mime_types_seen",
        "notes",
    ],
    "layout_cutovers": [
        "cutover_id",
        "era_start_estimate",
        "era_end_estimate",
        "old_pattern_or_layout",
        "new_pattern_or_layout",
        "last_old_capture_timestamp",
        "first_new_capture_timestamp",
        "evidence_old_capture_url",
        "evidence_new_capture_url",
        "signal_type",
        "confidence",
        "notes",
    ],
    "ranking_sources": [
        "source_id",
        "pattern_id",
        "original_url",
        "capture_timestamp",
        "capture_url",
        "ranking_type",
        "sort_param",
        "category",
        "page_number",
        "contains_ranked_game_list",
        "game_count_extracted",
        "fields_available",
        "parser_candidate",
        "confidence",
        "notes",
    ],
    "parser_signatures": [
        "signature_id",
        "era_start_estimate",
        "era_end_estimate",
        "sample_capture_url",
        "dom_markers",
        "css_markers",
        "js_markers",
        "ranking_container_selector",
        "game_card_selector",
        "title_selector",
        "rating_selector",
        "plays_selector",
        "pagination_selector",
        "parser_status",
        "confidence",
        "notes",
    ],
    "anomalies": [
        "anomaly_id",
        "timestamp",
        "url",
        "capture_url",
        "issue_type",
        "description",
        "severity",
        "resolution_status",
        "notes",
    ],
}


@dataclass(frozen=True)
class Capture:
    urlkey: str
    timestamp: str
    original: str
    mimetype: str
    statuscode: str
    digest: str
    length: str

    @property
    def capture_url(self) -> str:
        return WAYBACK_VIEW.format(timestamp=self.timestamp, original=self.original)

    @property
    def raw_url(self) -> str:
        return WAYBACK_RAW.format(timestamp=self.timestamp, original=self.original)

    @property
    def year(self) -> str:
        return self.timestamp[:4]

    @property
    def month(self) -> str:
        return self.timestamp[4:6]


def fetch_json(url: str, cache_path: Path, sleep_s: float = 0.8) -> list[dict[str, str]]:
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    req = urllib.request.Request(url, headers={"User-Agent": "KongregateWaybackPilot/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
        data = json.loads(payload)
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        (LOGS / "cdx_errors.log").open("a", encoding="utf-8").write(f"{datetime.utcnow().isoformat()}Z\t{url}\t{exc}\n")
        data = []
    if not data:
        rows: list[dict[str, str]] = []
    else:
        headers = data[0]
        rows = [dict(zip(headers, row)) for row in data[1:]]
    cache_path.write_text(json.dumps(rows, indent=2, sort_keys=True))
    time.sleep(sleep_s)
    return rows


def fetch_text(url: str, cache_path: Path, sleep_s: float = 0.8) -> str:
    if cache_path.exists():
        return cache_path.read_text(errors="replace")
    req = urllib.request.Request(url, headers={"User-Agent": "KongregateWaybackPilot/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
    except (TimeoutError, urllib.error.URLError) as exc:
        payload = ""
        (LOGS / "html_errors.log").open("a", encoding="utf-8").write(f"{datetime.utcnow().isoformat()}Z\t{url}\t{exc}\n")
    cache_path.write_text(payload)
    time.sleep(sleep_s)
    return payload


def cdx_url(original: str, collapse: str | None = None, limit: int | None = None) -> str:
    params = {
        "url": original,
        "output": "json",
        "fl": ",".join(FIELDS),
        "filter": ["statuscode:200", "mimetype:text/html"],
    }
    parts = []
    for key, value in params.items():
        if isinstance(value, list):
            for item in value:
                parts.append((key, item))
        else:
            parts.append((key, value))
    if collapse:
        parts.append(("collapse", collapse))
    if limit:
        parts.append(("limit", str(limit)))
    return f"{CDX_ENDPOINT}?{urllib.parse.urlencode(parts)}"


def safe_name(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", text).strip("_")[:160]


def normalize_original(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.netloc.lower()
    path = (parsed.path or "/").lower()
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    keep = [(k, v) for k, v in query_pairs if k in {"sort", "page", "category", "q"}]
    query = urllib.parse.urlencode(keep)
    return urllib.parse.urlunsplit(("https", host, path, query, ""))


def classify_pattern(url: str) -> tuple[str, str, str, str, str, str]:
    parsed = urllib.parse.urlsplit(url)
    path = parsed.path.rstrip("/") or "/"
    qs = dict(urllib.parse.parse_qsl(parsed.query))
    sort = qs.get("sort", "")
    page_style = "query_page" if "page=" in parsed.query else ""
    locale = "locale_prefixed" if path.startswith("/en/") else "none"
    category = ""
    ptype = "unknown"
    ranking_type = "unknown"
    if path == "/":
        ptype = "homepage"
        ranking_type = "homepage_module"
    elif path == "/games":
        ptype = "browse"
        ranking_type = {"rating": "top_rated", "plays": "most_played", "newest": "newest", "oldest": "oldest"}.get(sort, "unknown")
    elif path in {"/top-rated-games", "/best-games"}:
        ptype = "ranking"
        ranking_type = "top_rated"
    elif path == "/most-played-games":
        ptype = "ranking"
        ranking_type = "most_played"
    elif path == "/new-games":
        ptype = "ranking"
        ranking_type = "newest"
    elif path == "/hot-games":
        ptype = "ranking"
        ranking_type = "hot"
    else:
        match = re.match(r"^/(?:en/)?([a-z0-9-]+)-games$", path)
        if match:
            ptype = "category"
            category = match.group(1)
            ranking_type = "category_top"
    return ptype, ranking_type, sort, category, page_style, locale


def pattern_template(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    path = parsed.path.rstrip("/") or "/"
    qs = dict(urllib.parse.parse_qsl(parsed.query))
    if re.match(r"^/(?:en/)?[a-z0-9-]+-games$", path):
        path = re.sub(r"^/en/[a-z0-9-]+-games$", "/en/{genre}-games", path)
        path = re.sub(r"^/[a-z0-9-]+-games$", "/{genre}-games", path)
    query = ""
    keep = []
    for key in ("page", "sort"):
        if key in qs:
            keep.append((key, f"{{{key}}}"))
    if keep:
        query = "?" + "&".join(f"{key}={value}" for key, value in keep)
    return path + query


def week_start(timestamp: str) -> str:
    dt = datetime.strptime(timestamp[:8], "%Y%m%d").date()
    monday = dt - timedelta(days=dt.weekday())
    return monday.isoformat()


def choose_samples(captures: list[Capture], max_total: int = 5) -> list[Capture]:
    rows = sorted(captures, key=lambda c: c.timestamp)
    if len(rows) <= max_total:
        return rows
    indexes = {0, len(rows) - 1}
    if max_total >= 3:
        indexes.add(len(rows) // 2)
    if max_total >= 4:
        indexes.add(len(rows) // 3)
    if max_total >= 5:
        indexes.add((len(rows) * 2) // 3)
    return [rows[i] for i in sorted(indexes)][:max_total]


def extract_title(doc: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", doc, flags=re.I | re.S)
    if not match:
        return ""
    return html.unescape(re.sub(r"\s+", " ", match.group(1)).strip())


def html_signature(doc: str) -> dict[str, str | int | bool]:
    classes = set(re.findall(r'class=["\']([^"\']+)["\']', doc, flags=re.I))
    class_words = set()
    for cls in classes:
        class_words.update(cls.split())
    css = re.findall(r'href=["\']([^"\']+\.css[^"\']*)["\']', doc, flags=re.I)
    js = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', doc, flags=re.I)
    links = re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', doc, flags=re.I | re.S)
    game_links = []
    for href, label in links:
        if re.search(r"/games/[^/]+/[^/?#]+", href):
            text = html.unescape(re.sub(r"<[^>]+>", "", label))
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                game_links.append((href, text))
    marker_candidates = [
        "game",
        "game_browser",
        "game_browser_item",
        "game-card",
        "game-list",
        "browse_game",
        "rating",
        "plays",
        "pagination",
        "sort",
        "browse",
    ]
    markers = sorted([m for m in marker_candidates if m in doc or m in class_words])
    return {
        "title": extract_title(doc),
        "dom_markers": ",".join(markers[:20]),
        "css_markers": ",".join(css[:8]),
        "js_markers": ",".join(js[:8]),
        "game_link_count": len({href for href, _ in game_links}),
        "has_rating": bool(re.search(r"rating|stars?|rated", doc, flags=re.I)),
        "has_plays": bool(re.search(r"plays?|played", doc, flags=re.I)),
        "has_pagination": bool(re.search(r"pagination|next|previous|page=", doc, flags=re.I)),
    }


def html_cache_path(cap: Capture) -> Path:
    digest = hashlib.sha1(f"{cap.timestamp}:{cap.original}".encode()).hexdigest()[:16]
    return RAW_HTML / f"{cap.timestamp}_{safe_name(cap.original)}_{digest}.html"


def write_csv(name: str, rows: list[dict[str, object]]) -> None:
    cols = TAB_COLUMNS[name]
    path = PROCESSED / f"{name}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in cols})


def main() -> None:
    for path in (RAW_CDX, RAW_HTML, PROCESSED, LOGS):
        path.mkdir(parents=True, exist_ok=True)

    seed_urls = list(SEED_URLS)
    for genre in PILOT_GENRES:
        seed_urls.append((f"{genre}_games", f"https://www.kongregate.com/{genre}-games"))
        seed_urls.append((f"en_{genre}_games", f"https://www.kongregate.com/en/{genre}-games"))

    all_captures: dict[str, list[Capture]] = {}
    for seed_id, original in seed_urls:
        cache = RAW_CDX / f"{seed_id}.json"
        rows = fetch_json(cdx_url(original, collapse="digest"), cache)
        captures = [Capture(**row) for row in rows]
        all_captures[original] = captures

    pattern_groups: dict[str, list[Capture]] = defaultdict(list)
    for captures in all_captures.values():
        for cap in captures:
            pattern_groups[pattern_template(normalize_original(cap.original))].append(cap)

    url_patterns = []
    pattern_ids: dict[str, str] = {}
    for index, (template, captures) in enumerate(sorted(pattern_groups.items()), start=1):
        captures = sorted(captures, key=lambda c: c.timestamp)
        first = captures[0]
        last = captures[-1]
        ptype, _ranking_type, sort, category, page_style, locale = classify_pattern(normalize_original(first.original))
        pattern_id = f"pat_{index:03d}"
        pattern_ids[template] = pattern_id
        url_patterns.append(
            {
                "pattern_id": pattern_id,
                "pattern_template": template,
                "example_url": normalize_original(first.original),
                "first_seen_timestamp": first.timestamp,
                "last_seen_timestamp": last.timestamp,
                "status": "archived_only",
                "pattern_type": ptype,
                "sort_param": sort,
                "category_param": category if "{genre}" not in template else "{genre}",
                "pagination_style": page_style,
                "locale_style": locale,
                "evidence_capture_url": first.capture_url,
                "confidence": "medium" if len(captures) > 1 else "low",
                "notes": f"Observed in pilot CDX query; {len(captures)} digest-distinct HTML captures.",
            }
        )

    coverage_buckets: dict[tuple[str, str, str, str, str], list[Capture]] = defaultdict(list)
    for original, captures in all_captures.items():
        template = pattern_template(normalize_original(original))
        pid = pattern_ids.get(template, "")
        for cap in captures:
            coverage_buckets[(pid, original, cap.year, cap.month, week_start(cap.timestamp))].append(cap)

    capture_coverage = []
    for (pid, original, year, month, week), captures in sorted(coverage_buckets.items()):
        captures = sorted(captures, key=lambda c: c.timestamp)
        capture_coverage.append(
            {
                "pattern_id": pid,
                "original_url": original,
                "year": year,
                "month": month,
                "week_start": week,
                "capture_count": len(captures),
                "usable_html_count": sum(1 for c in captures if c.statuscode == "200" and c.mimetype == "text/html"),
                "first_capture_timestamp": captures[0].timestamp,
                "last_capture_timestamp": captures[-1].timestamp,
                "sample_capture_url": captures[0].capture_url,
                "status_codes_seen": ",".join(sorted({c.statuscode for c in captures})),
                "mime_types_seen": ",".join(sorted({c.mimetype for c in captures})),
                "notes": "Digest-collapsed pilot coverage bucket.",
            }
        )

    ranking_sources = []
    parser_signatures = []
    anomalies = []
    sampled_caps: list[tuple[str, Capture, dict[str, str | int | bool]]] = []

    for original, captures in all_captures.items():
        for cap in choose_samples(captures, max_total=5):
            cache = html_cache_path(cap)
            doc = fetch_text(cap.raw_url, cache)
            sig = html_signature(doc)
            sampled_caps.append((original, cap, sig))
            norm = normalize_original(original)
            template = pattern_template(norm)
            pid = pattern_ids.get(template, "")
            ptype, ranking_type, sort, category, _page_style, _locale = classify_pattern(norm)
            contains_ranked = bool(sig["game_link_count"]) and ptype in {"homepage", "browse", "category", "ranking"}
            fields = ["title", "game_url"]
            if sig["has_rating"]:
                fields.append("rating")
            if sig["has_plays"]:
                fields.append("plays")
            if re.search(r"developer|by\s+<|/accounts/", doc, flags=re.I):
                fields.append("developer")
            if re.search(r"<img|thumbnail|preview", doc, flags=re.I):
                fields.append("thumbnail")
            ranking_sources.append(
                {
                    "source_id": f"src_{len(ranking_sources) + 1:04d}",
                    "pattern_id": pid,
                    "original_url": original,
                    "capture_timestamp": cap.timestamp,
                    "capture_url": cap.capture_url,
                    "ranking_type": ranking_type,
                    "sort_param": sort,
                    "category": category,
                    "page_number": "",
                    "contains_ranked_game_list": "yes" if contains_ranked else "no",
                    "game_count_extracted": sig["game_link_count"],
                    "fields_available": ",".join(fields) if contains_ranked else "",
                    "parser_candidate": "server_rendered_links" if contains_ranked else "needs_manual_review",
                    "confidence": "medium" if contains_ranked and int(sig["game_link_count"]) >= 10 else "low",
                    "notes": f"Title: {sig['title']}; raw HTML cached at {cache.relative_to(ROOT)}",
                }
            )
            if not doc.strip() or "Wayback Machine has not archived that URL" in doc:
                anomalies.append(
                    {
                        "anomaly_id": f"anom_{len(anomalies) + 1:04d}",
                        "timestamp": cap.timestamp,
                        "url": original,
                        "capture_url": cap.capture_url,
                        "issue_type": "wayback_error",
                        "description": "Raw capture returned empty or Wayback error content.",
                        "severity": "medium",
                        "resolution_status": "open",
                        "notes": str(cache.relative_to(ROOT)),
                    }
                )

    by_era: dict[str, list[tuple[str, Capture, dict[str, str | int | bool]]]] = defaultdict(list)
    for row in sampled_caps:
        year = row[1].year
        era = f"{year[:3]}0s" if year < "2010" else year
        by_era[era].append(row)
    for index, (era, rows) in enumerate(sorted(by_era.items()), start=1):
        _original, cap, sig = rows[0]
        parser_signatures.append(
            {
                "signature_id": f"sig_{index:03d}",
                "era_start_estimate": min(r[1].timestamp for r in rows),
                "era_end_estimate": max(r[1].timestamp for r in rows),
                "sample_capture_url": cap.capture_url,
                "dom_markers": sig["dom_markers"],
                "css_markers": sig["css_markers"],
                "js_markers": sig["js_markers"],
                "ranking_container_selector": "",
                "game_card_selector": "a[href*='/games/']",
                "title_selector": "a[href*='/games/']",
                "rating_selector": "text/regex: rating|rated|stars",
                "plays_selector": "text/regex: plays|played",
                "pagination_selector": "text/regex: pagination|next|previous; a[href*='page=']",
                "parser_status": "candidate",
                "confidence": "low",
                "notes": f"Pilot signature from title '{sig['title']}' with {sig['game_link_count']} game links.",
            }
        )

    layout_cutovers = []
    sorted_sigs = sorted(parser_signatures, key=lambda r: r["era_start_estimate"])
    for prev, curr in zip(sorted_sigs, sorted_sigs[1:]):
        if prev["dom_markers"] != curr["dom_markers"] or prev["css_markers"] != curr["css_markers"]:
            layout_cutovers.append(
                {
                    "cutover_id": f"cut_{len(layout_cutovers) + 1:03d}",
                    "era_start_estimate": prev["era_end_estimate"],
                    "era_end_estimate": curr["era_start_estimate"],
                    "old_pattern_or_layout": prev["dom_markers"] or "unknown markers",
                    "new_pattern_or_layout": curr["dom_markers"] or "unknown markers",
                    "last_old_capture_timestamp": prev["era_end_estimate"],
                    "first_new_capture_timestamp": curr["era_start_estimate"],
                    "evidence_old_capture_url": prev["sample_capture_url"],
                    "evidence_new_capture_url": curr["sample_capture_url"],
                    "signal_type": "html_layout_change",
                    "confidence": "low",
                    "notes": "Automated pilot diff; requires manual confirmation with denser samples.",
                }
            )

    tables = {
        "url_patterns": url_patterns,
        "capture_coverage": capture_coverage,
        "layout_cutovers": layout_cutovers,
        "ranking_sources": ranking_sources,
        "parser_signatures": parser_signatures,
        "anomalies": anomalies,
    }
    for name, rows in tables.items():
        write_csv(name, rows)
    (PROCESSED / "tables.json").write_text(json.dumps({"columns": TAB_COLUMNS, "tables": tables}, indent=2))

    report = {
        "run_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed_url_count": len(seed_urls),
        "cdx_records_processed": sum(len(captures) for captures in all_captures.values()),
        "patterns_discovered": len(url_patterns),
        "candidate_ranking_sources_found": sum(1 for row in ranking_sources if row["contains_ranked_game_list"] == "yes"),
        "html_samples_cached": len(sampled_caps),
        "suspected_cutovers": len(layout_cutovers),
        "anomalies": len(anomalies),
        "recommended_next_queries": [
            "Run prefix CDX queries for https://www.kongregate.com/games* without digest collapse.",
            "Add quarterly homepage snapshots and manually verify layout_cutovers around detected boundaries.",
            "Expand category pages with page=N and sort=rating/plays once parser signatures are confirmed.",
        ],
    }
    (LOGS / "pilot_run_report.json").write_text(json.dumps(report, indent=2))
    (LOGS / "pilot_run_report.md").write_text(
        "\n".join(
            [
                "# Kongregate Wayback Pilot Run Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- Seed URLs queried: {report['seed_url_count']}",
                f"- CDX records processed: {report['cdx_records_processed']}",
                f"- Patterns discovered: {report['patterns_discovered']}",
                f"- Candidate ranking sources found: {report['candidate_ranking_sources_found']}",
                f"- HTML samples cached: {report['html_samples_cached']}",
                f"- Suspected cutovers: {report['suspected_cutovers']}",
                f"- Anomalies: {report['anomalies']}",
                "",
                "## Recommended Next Queries",
                "",
                *[f"- {item}" for item in report["recommended_next_queries"]],
                "",
            ]
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
