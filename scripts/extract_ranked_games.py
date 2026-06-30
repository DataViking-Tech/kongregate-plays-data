#!/usr/bin/env python3
"""Extract date/game/rank rows from cached Kongregate Wayback HTML samples."""

from __future__ import annotations

import csv
import html
import json
import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from lxml import html as lxml_html


ROOT = Path(__file__).resolve().parents[1]
RAW_HTML = ROOT / "data" / "raw" / "html"
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

OUTPUT_CSV = PROCESSED / "ranked_games.csv"
OUTPUT_JSON = PROCESSED / "ranked_games.json"
REPORT_JSON = LOGS / "ranked_games_report.json"
REPORT_MD = LOGS / "ranked_games_report.md"
HTML_MANIFEST = RAW_HTML / "manifest.json"

RANKED_COLUMNS = [
    "date",
    "game_name",
    "rank_on_date",
    "ranking_type",
    "ranking_basis",
    "plays_count_observed",
    "plays_rank_within_capture",
    "plays_rank_scope",
    "category",
    "source_url",
    "capture_timestamp",
    "capture_url",
    "game_url",
    "developer",
    "rating_text",
    "plays_text",
    "parser",
    "confidence",
    "notes",
]

WAYBACK_VIEW = "https://web.archive.org/web/{timestamp}/{original}"


@dataclass(frozen=True)
class HtmlSample:
    path: Path
    capture_timestamp: str
    original_url: str

    @property
    def capture_date(self) -> str:
        return datetime.strptime(self.capture_timestamp[:8], "%Y%m%d").date().isoformat()

    @property
    def capture_url(self) -> str:
        return WAYBACK_VIEW.format(timestamp=self.capture_timestamp, original=self.original_url)


def strip_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def class_contains(element, class_name: str) -> bool:
    classes = (element.get("class") or "").split()
    return class_name in classes


def href_is_game(href: str | None) -> bool:
    if not href:
        return False
    return bool(re.search(r"/(?:en/)?games/[^/?#]+/[^/?#]+", href))


def absolutize_game_url(href: str, source_url: str) -> str:
    url = urllib.parse.urljoin(source_url, href)
    parsed = urllib.parse.urlsplit(url)
    parsed = parsed._replace(query="", fragment="")
    return urllib.parse.urlunsplit(parsed)


def infer_original_from_filename(path: Path, doc: str) -> tuple[str, str]:
    timestamp_match = re.match(r"^(\d{14})_", path.name)
    timestamp = timestamp_match.group(1) if timestamp_match else ""
    canonical = ""
    canon_matches = re.findall(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', doc, flags=re.I)
    if canon_matches:
        canonical = html.unescape(canon_matches[0])
    if not canonical:
        og_matches = re.findall(r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']', doc, flags=re.I)
        if og_matches:
            canonical = html.unescape(og_matches[0])
    if canonical:
        return timestamp, canonical

    name_body = re.sub(r"^\d{14}_", "", path.stem)
    name_body = re.sub(r"_[0-9a-f]{16}$", "", name_body)
    sort_match = re.match(r"^(https?)_(.+?)_games_sort_([a-z]+)$", name_body)
    if sort_match:
        scheme, host_part, sort_value = sort_match.groups()
        host = host_part.replace("_80", ":80").replace("_", ".")
        return timestamp, f"{scheme}://{host}/games?sort={sort_value}"
    if name_body.startswith("http_"):
        original = "http://" + name_body[5:].replace("_", "/")
    elif name_body.startswith("https_"):
        original = "https://" + name_body[6:].replace("_", "/")
    else:
        original = "https://www.kongregate.com/"
    original = original.replace("www.kongregate.com/80/", "www.kongregate.com:80/")
    original = original.replace("kongregate.com/80/", "kongregate.com:80/")
    return timestamp, original


def infer_source_fields(source_url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlsplit(source_url)
    path = parsed.path.rstrip("/").lower() or "/"
    query = dict(urllib.parse.parse_qsl(parsed.query))
    sort = query.get("sort", "")
    category = ""
    ranking_type = "unknown"
    if path == "/":
        ranking_type = "homepage_module"
    elif path in {"/top-rated-games", "/best-games"}:
        ranking_type = "top_rated"
    elif path == "/popular_games" and sort == "date":
        ranking_type = "newest" if query.get("reverse", "").lower() == "true" else "oldest"
    elif path in {"/most-played-games", "/popular_games"}:
        ranking_type = "most_played"
    elif path == "/new-games":
        ranking_type = "newest"
    elif path == "/hot-games":
        ranking_type = "hot"
    elif path == "/games":
        ranking_type = {"rating": "top_rated", "gameplays": "most_played", "plays": "most_played", "newest": "newest", "oldest": "oldest"}.get(sort, "browse")
    else:
        match = re.match(r"^/(?:en/)?([a-z0-9-]+)-games(?:/slider)?$", path)
        if match:
            ranking_type = "category_top"
            category = match.group(1)
    return ranking_type, category


def first_text(element, xpaths: list[str]) -> str:
    for xpath in xpaths:
        values = element.xpath(xpath)
        for value in values:
            if hasattr(value, "text_content"):
                text = strip_text(value.text_content())
            else:
                text = strip_text(str(value))
            if text:
                return text
    return ""


def first_href_and_text(element, xpaths: list[str], source_url: str) -> tuple[str, str]:
    for xpath in xpaths:
        values = element.xpath(xpath)
        for node in values:
            if not hasattr(node, "get"):
                continue
            href = node.get("href")
            text = strip_text(node.text_content())
            if re.search(r"^\d[\d,.]*\s*[kmb]?\s+(?:gameplays|plays|played)\b", text, flags=re.I):
                continue
            if href_is_game(href) and text and text.lower() not in {"play now »", "play now", "games"}:
                return absolutize_game_url(href, source_url), text
    return "", ""


def rating_text(element) -> str:
    text = first_text(element, [
        ".//*[contains(concat(' ', normalize-space(@class), ' '), ' current-rating ')]/text()",
        ".//*[contains(concat(' ', normalize-space(@class), ' '), ' star-rating ')]//text()",
    ])
    style_values = element.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' current-rating ')]/@style")
    if text:
        return text
    if style_values:
        return strip_text(style_values[0])
    return ""


def plays_text(element) -> str:
    texts = element.xpath(".//a[contains(@href, '/games/')]/text() | .//text()")
    for text in texts:
        cleaned = strip_text(text)
        if re.search(r"\bgameplays\b|\bplays\b|\bplayed\b", cleaned, flags=re.I):
            return cleaned.replace("\xa0", " ")
    return ""


def parse_plays_count(value: str) -> int | str:
    match = re.search(r"(\d+(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*([kmb])?\s+(?:gameplays|plays|played)\b", value or "", flags=re.I)
    if not match:
        return ""
    number_text, unit = match.groups()
    number = float(number_text.replace(",", ""))
    multiplier = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}.get((unit or "").lower(), 1)
    return int(round(number * multiplier))


def ranking_basis_for(ranking_type: str) -> str:
    if ranking_type == "most_played":
        return "page_order_most_played"
    if ranking_type == "top_rated":
        return "page_order_top_rated"
    if ranking_type == "newest":
        return "page_order_newest"
    if ranking_type == "oldest":
        return "page_order_oldest"
    if ranking_type == "category_top":
        return "page_order_category_default"
    if ranking_type == "browse":
        return "page_order_browse_default"
    return "page_order_observed"


def add_play_ranks(rows: list[dict[str, object]]) -> None:
    ranked = sorted(
        [row for row in rows if isinstance(row.get("plays_count_observed"), int)],
        key=lambda row: int(row["plays_count_observed"]),
        reverse=True,
    )
    previous_count = None
    previous_rank = 0
    for position, row in enumerate(ranked, start=1):
        count = row["plays_count_observed"]
        rank = previous_rank if count == previous_count else position
        row["plays_rank_within_capture"] = rank
        row["plays_rank_scope"] = "visible_games_in_same_capture"
        previous_count = count
        previous_rank = rank


def developer_text(element) -> str:
    value = first_text(element, [
        ".//a[contains(concat(' ', normalize-space(@class), ' '), ' dev_name ')]/text()",
        ".//*[contains(concat(' ', normalize-space(@class), ' '), ' developer ')]//a/text()",
        ".//p[contains(concat(' ', normalize-space(@class), ' '), ' info ')]/strong/text()",
    ])
    return re.sub(r"^by\s+", "", value, flags=re.I)


def extract_card(element, source_url: str) -> dict[str, str] | None:
    game_url, title = first_href_and_text(element, [
        ".//a[contains(concat(' ', normalize-space(@class), ' '), ' game_title ')]",
        ".//a[@itemprop='name']",
        ".//strong[contains(concat(' ', normalize-space(@class), ' '), ' title ')]//a",
        ".//dl[contains(concat(' ', normalize-space(@class), ' '), ' description ')]/dt/a",
        ".//a[contains(@href, '/games/') and not(.//img)]",
        ".//a[contains(@href, '/en/games/') and not(.//img)]",
    ], source_url)
    if not title:
        image_titles = element.xpath(".//a[contains(@href, '/games/') or contains(@href, '/en/games/')]//img/@title")
        if image_titles:
            title = strip_text(image_titles[0])
            hrefs = element.xpath(".//a[contains(@href, '/games/') or contains(@href, '/en/games/')]/@href")
            if hrefs:
                game_url = absolutize_game_url(hrefs[0], source_url)
    if not title or not game_url:
        return None
    return {
        "game_name": title,
        "game_url": game_url,
        "developer": developer_text(element),
        "rating_text": rating_text(element),
        "plays_text": plays_text(element),
    }


def document_order_key(element) -> tuple[int, ...]:
    return tuple(int(part) for part in element.getroottree().getpath(element).replace("[", "/").replace("]", "").split("/") if part.isdigit())


def extract_game_listing(doc, source_url: str) -> tuple[list[dict[str, str]], str, str]:
    listings = doc.xpath("//div[contains(concat(' ', normalize-space(@class), ' '), ' game_listing ')]")
    if not listings:
        return [], "", ""
    listing = listings[0]
    elements = []
    for element in listing.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' game_row ')]"):
        elements.append(element)
    for element in listing.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' game ')]"):
        if any(parent in elements for parent in element.iterancestors()):
            continue
        if element.xpath(".//a[contains(@href, '/games/') or contains(@href, '/en/games/')]"):
            elements.append(element)
    elements = sorted(elements, key=document_order_key)
    rows = []
    seen = set()
    for element in elements:
        card = extract_card(element, source_url)
        if not card or card["game_url"] in seen:
            continue
        seen.add(card["game_url"])
        rows.append(card)
    return rows, "game_listing", "high" if len(rows) >= 10 else "medium"


def extract_game_browser_rows(doc, source_url: str) -> tuple[list[dict[str, str]], str, str]:
    rows_by_rank: list[tuple[int, dict[str, str]]] = []
    for element in doc.xpath("//div[starts-with(@id, 'game_browser_game_row_')]"):
        match = re.search(r"game_browser_game_row_(\d+)", element.get("id") or "")
        if not match:
            continue
        card = extract_card(element, source_url)
        if not card:
            continue
        rows_by_rank.append((int(match.group(1)), card))
    if not rows_by_rank:
        return [], "", ""
    rows = [card for _rank, card in sorted(rows_by_rank, key=lambda item: item[0])]
    confidence = "high" if len(rows) >= 10 else "medium"
    return rows, "game_browser_game_row", confidence


def extract_legacy_game_blocks(doc, source_url: str) -> tuple[list[dict[str, str]], str, str]:
    parsed = urllib.parse.urlsplit(source_url)
    containers = []
    if parsed.path.rstrip("/").lower() == "/games":
        containers = doc.xpath("//*[@id='popular']")
    if not containers:
        containers = [doc]

    elements = []
    for container in containers:
        elements.extend(container.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' game ')]"))
    if not elements:
        return [], "", ""

    rows = []
    seen = set()
    for element in sorted(elements, key=document_order_key):
        card = extract_card(element, source_url)
        if not card or card["game_url"] in seen:
            continue
        seen.add(card["game_url"])
        rows.append(card)
    if not rows:
        return [], "", ""
    confidence = "high" if len(rows) >= 10 else "medium"
    return rows, "legacy_game_blocks", confidence


def extract_legacy_games_table(doc, source_url: str) -> tuple[list[dict[str, str]], str, str]:
    table_rows = doc.xpath("//table[@id='games']//tbody/tr")
    if not table_rows:
        return [], "", ""

    rows = []
    seen = set()
    for element in table_rows:
        game_url, title = first_href_and_text(element, [
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' first ')]//a[contains(@href, '/games/') and not(.//img)]",
            ".//a[contains(@href, '/games/') and not(.//img)]",
        ], source_url)
        if not game_url or not title or game_url in seen:
            continue
        seen.add(game_url)
        developer = first_text(element, [
            ".//td[3]//a[contains(@href, '/accounts/')]/text()",
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' developer ')]//a/text()",
        ])
        rows.append(
            {
                "game_name": title,
                "game_url": game_url,
                "developer": developer,
                "rating_text": rating_text(element),
                "plays_text": plays_text(element),
            }
        )
    if not rows:
        return [], "", ""
    confidence = "high" if len(rows) >= 10 else "medium"
    return rows, "legacy_games_table", confidence


def extract_modern_cards(doc, source_url: str) -> tuple[list[dict[str, str]], str, str]:
    elements = doc.xpath(
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' game-tile ')]"
        " | //div[contains(concat(' ', normalize-space(@class), ' '), ' game-card ')]"
        " | //k-game-card"
        " | //a[contains(@href, '/en/games/') and @title]"
    )
    rows = []
    seen = set()
    for element in elements:
        if element.tag == "div":
            hrefs = element.xpath(".//a[contains(@href, '/games/') or contains(@href, '/en/games/')]/@href")
            href = hrefs[0] if hrefs else ""
            title = first_text(element, [
                ".//a[contains(@href, '/games/') or contains(@href, '/en/games/')]//img/@alt",
                ".//*[@itemprop='name']/text()",
                ".//h3/text()",
                ".//*[contains(concat(' ', normalize-space(@class), ' '), ' font-semibold ')]/text()",
            ])
            text = strip_text(element.text_content())
            rating_match = re.search(r"★\s*([0-9]+(?:\.[0-9]+)?)", text)
            card = {
                "game_name": title,
                "game_url": absolutize_game_url(href, source_url) if href_is_game(href) else "",
                "developer": "",
                "rating_text": rating_match.group(1) if rating_match else rating_text(element),
                "plays_text": plays_text(element),
            } if href and title else None
        elif element.tag == "k-game-card":
            href = element.get("href") or element.get("url")
            title = element.get("title") or element.get("name") or first_text(element, [
                ".//*[@slot='title']/text()",
                ".//img/@title",
            ])
            if href and title and href_is_game(href):
                card = {
                    "game_name": strip_text(title),
                    "game_url": absolutize_game_url(href, source_url),
                    "developer": first_text(element, [".//k-card-byline/text()"]),
                    "rating_text": first_text(element, [".//k-card-status-action[@type='rating']/text()"]),
                    "plays_text": plays_text(element),
                }
            else:
                card = extract_card(element, source_url)
        else:
            href = element.get("href")
            title = element.get("title") or strip_text(element.text_content())
            card = {"game_name": strip_text(title), "game_url": absolutize_game_url(href, source_url), "developer": "", "rating_text": "", "plays_text": ""} if href_is_game(href) else None
        if not card or card["game_url"] in seen:
            continue
        seen.add(card["game_url"])
        rows.append(card)
    confidence = "medium" if len(rows) >= 10 else "low"
    return rows, "modern_card_links", confidence


def extract_rows(sample: HtmlSample, doc_text: str) -> tuple[list[dict[str, str]], str, str]:
    try:
        doc = lxml_html.fromstring(doc_text)
    except Exception:
        return [], "parse_error", "low"
    source_url = sample.original_url
    extractors = [extract_game_listing, extract_game_browser_rows, extract_modern_cards]
    best_rows: list[dict[str, str]] = []
    best_parser = "no_ranked_list"
    best_confidence = "low"
    for extractor in extractors:
        rows, parser, confidence = extractor(doc, source_url)
        if len(rows) > len(best_rows):
            best_rows = rows
            best_parser = parser
            best_confidence = confidence
    if not best_rows:
        for fallback_extractor in (extract_legacy_games_table, extract_legacy_game_blocks):
            best_rows, best_parser, best_confidence = fallback_extractor(doc, source_url)
            if best_rows:
                break
    return best_rows, best_parser, best_confidence


def play_count_note(parser: str, row: dict[str, str]) -> str:
    if row.get("plays_text"):
        return ""
    if parser == "game_browser_game_row":
        return "Play count not present in this game-browser layout HTML."
    return ""


def iter_samples() -> list[HtmlSample]:
    samples = []
    manifest = json.loads(HTML_MANIFEST.read_text()) if HTML_MANIFEST.exists() else {}
    for path in sorted(RAW_HTML.glob("*.html")):
        doc = path.read_text(errors="replace")
        manifest_row = manifest.get(str(path.relative_to(ROOT)), {})
        timestamp = manifest_row.get("capture_timestamp", "")
        original = manifest_row.get("original_url", "")
        if not timestamp or not original:
            timestamp, original = infer_original_from_filename(path, doc)
        if not timestamp:
            continue
        ranking_type, category = infer_source_fields(original)
        if ranking_type == "unknown" or ranking_type == "homepage_module":
            continue
        samples.append(HtmlSample(path=path, capture_timestamp=timestamp, original_url=original))
    return samples


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    output_rows = []
    sample_reports = []
    for sample in iter_samples():
        doc_text = sample.path.read_text(errors="replace")
        ranking_type, category = infer_source_fields(sample.original_url)
        rows, parser, confidence = extract_rows(sample, doc_text)
        sample_output_rows = []
        for rank, row in enumerate(rows, start=1):
            notes = f"Extracted from cached HTML {sample.path.relative_to(ROOT)}"
            missing_count_note = play_count_note(parser, row)
            if missing_count_note:
                notes = f"{notes}; {missing_count_note}"
            sample_output_rows.append(
                {
                    "date": sample.capture_date,
                    "game_name": row["game_name"],
                    "rank_on_date": rank,
                    "ranking_type": ranking_type,
                    "ranking_basis": ranking_basis_for(ranking_type),
                    "plays_count_observed": parse_plays_count(row["plays_text"]),
                    "plays_rank_within_capture": "",
                    "plays_rank_scope": "",
                    "category": category,
                    "source_url": sample.original_url,
                    "capture_timestamp": sample.capture_timestamp,
                    "capture_url": sample.capture_url,
                    "game_url": row["game_url"],
                    "developer": row["developer"],
                    "rating_text": row["rating_text"],
                    "plays_text": row["plays_text"],
                    "parser": parser,
                    "confidence": confidence,
                    "notes": notes,
                }
            )
        add_play_ranks(sample_output_rows)
        output_rows.extend(sample_output_rows)
        sample_reports.append(
            {
                "date": sample.capture_date,
                "source_url": sample.original_url,
                "capture_timestamp": sample.capture_timestamp,
                "parser": parser,
                "rows_extracted": len(rows),
                "confidence": confidence,
                "html_path": str(sample.path.relative_to(ROOT)),
            }
        )

    output_rows.sort(key=lambda row: (row["date"], row["ranking_type"], row["category"], row["source_url"], int(row["rank_on_date"])))

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RANKED_COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)
    OUTPUT_JSON.write_text(json.dumps({"columns": RANKED_COLUMNS, "rows": output_rows, "sample_reports": sample_reports}, indent=2))

    report = {
        "run_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "html_samples_considered": len(sample_reports),
        "ranking_rows_extracted": len(output_rows),
        "rows_with_observed_play_counts": sum(1 for row in output_rows if isinstance(row.get("plays_count_observed"), int)),
        "captures_with_rows": sum(1 for report_row in sample_reports if report_row["rows_extracted"] > 0),
        "captures_without_rows": sum(1 for report_row in sample_reports if report_row["rows_extracted"] == 0),
        "ranking_types": sorted({row["ranking_type"] for row in output_rows}),
        "first_date": output_rows[0]["date"] if output_rows else "",
        "last_date": output_rows[-1]["date"] if output_rows else "",
    }
    REPORT_JSON.write_text(json.dumps({"summary": report, "samples": sample_reports}, indent=2))
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Kongregate Ranked Games Extraction Report",
                "",
                f"- Run timestamp: {report['run_timestamp']}",
                f"- HTML samples considered: {report['html_samples_considered']}",
                f"- Ranking rows extracted: {report['ranking_rows_extracted']}",
                f"- Rows with observed play counts: {report['rows_with_observed_play_counts']}",
                f"- Captures with rows: {report['captures_with_rows']}",
                f"- Captures without rows: {report['captures_without_rows']}",
                f"- Ranking types: {', '.join(report['ranking_types'])}",
                f"- Date range: {report['first_date']} to {report['last_date']}",
                "",
                "The main output is `data/processed/ranked_games.csv`; its first three columns are `date`, `game_name`, and `rank_on_date`.",
                "",
            ]
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
