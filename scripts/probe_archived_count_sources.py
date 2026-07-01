#!/usr/bin/env python3
"""Probe archived Kongregate side endpoints for hidden play-count sources."""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import re
import signal
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path

from kongregate_canonical import canonical_game_url


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_GAME_PAGES = ROOT / "data" / "raw" / "game_pages"
RAW_PROBE = ROOT / "data" / "raw" / "count_source_probe"
RAW_CDX = RAW_PROBE / "cdx"
RAW_PAYLOADS = RAW_PROBE / "payloads"
LOGS = ROOT / "logs"

DEFAULT_INPUT_CSV = PROCESSED / "metrics_no_cdx_profile.csv"
GAME_STATUS_CSV = PROCESSED / "count_source_probe_game_status.csv"
GAME_PAGE_MANIFEST = RAW_GAME_PAGES / "manifest.json"
GAME_PAGE_FAILURES = RAW_GAME_PAGES / "failures.json"
REPORT_JSON = LOGS / "count_source_probe_report.json"
REPORT_MD = LOGS / "count_source_probe_report.md"
CANDIDATES_CSV = PROCESSED / "count_source_probe_candidates.csv"
HISTORY_CSV = PROCESSED / "count_source_probe_history.csv"
PLAY_COUNTS_CSV = PROCESSED / "count_source_play_counts.csv"
ERROR_LOG = LOGS / "count_source_probe_errors.log"

CDX_ENDPOINT = "https://web.archive.org/cdx"
WAYBACK_RAW = "https://web.archive.org/web/{timestamp}id_/{original}"
CDX_FIELDS = ["timestamp", "original", "statuscode", "mimetype", "digest", "length"]
CSV_COLUMNS = [
    "game_name",
    "game_url",
    "source_page_timestamp",
    "source_page_path",
    "source_type",
    "endpoint_url",
    "cdx_status",
    "cdx_rows",
    "sample_timestamp",
    "sample_original",
    "sample_mimetype",
    "sample_path",
    "count_signal",
    "parsed_plays",
    "notes",
]
HISTORY_COLUMNS = [
    "first_probe_run_timestamp",
    "last_probe_run_timestamp",
    "probe_seen_count",
    *CSV_COLUMNS,
]


class RequestWallClockTimeout(TimeoutError):
    pass


@contextmanager
def wall_clock_timeout(seconds: float):
    if seconds <= 0 or not hasattr(signal, "setitimer"):
        yield
        return

    def timeout_handler(_signum, _frame):
        raise RequestWallClockTimeout(f"wall_clock_timeout_{seconds:g}s")

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)
        signal.signal(signal.SIGALRM, previous_handler)


@dataclass(frozen=True)
class TargetGame:
    game_name: str
    game_url: str
    canonical_key: str
    game_ids: tuple[str, ...]
    tier: int
    best_rank: int
    first_seen_date: str
    last_seen_date: str


@dataclass(frozen=True)
class PageRef:
    game_name: str
    game_url: str
    canonical_key: str
    timestamp: str
    original_url: str
    relative_path: str
    page_status: str


@dataclass(frozen=True)
class EndpointCandidate:
    game: TargetGame
    page: PageRef
    source_type: str
    endpoint_url: str
    discovered_from: str


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def sha(text: str, length: int = 16) -> str:
    return sha1(text.encode("utf-8")).hexdigest()[:length]


def safe_name(text: str) -> str:
    text = urllib.parse.unquote(text).replace("?sort=", "_sort_")
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", text).strip("_")[:170]


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value or "")
    match = re.search(r"\d[\d,]*", text)
    if not match:
        return 0
    return int(match.group(0).replace(",", ""))


def cdx_status_prefix(value: object) -> str:
    return str(value or "").split(":", 1)[0] or "unknown"


def parse_date(value: str):
    text = str(value or "")[:10]
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_timestamp_date(value: str):
    text = str(value or "")[:8]
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None


def timestamp_from_date(value: str) -> str:
    capture_date = parse_date(value)
    if not capture_date:
        return ""
    return capture_date.strftime("%Y%m%d000000")


def page_distance(game: TargetGame, page: PageRef) -> int:
    capture_date = parse_timestamp_date(page.timestamp)
    first_seen = parse_date(game.first_seen_date)
    last_seen = parse_date(game.last_seen_date) or first_seen
    if not capture_date or not first_seen or not last_seen:
        return 0
    if first_seen <= capture_date <= last_seen:
        return 0
    return min(abs((capture_date - first_seen).days), abs((capture_date - last_seen).days))


def js_unescape(value: str) -> str:
    return html.unescape(value).replace("\\/", "/").replace("\\u0026", "&")


def csv_list(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def load_status_filter_keys(status_csv: Path, statuses: set[str]) -> set[str] | None:
    if not statuses:
        return None
    if not status_csv.exists():
        raise SystemExit(f"Status filter requested, but {relative(status_csv)} does not exist. Run summarize_count_source_probe_history.py first.")
    keys: set[str] = set()
    with status_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            status = str(row.get("status", "")).strip().lower()
            if status not in statuses:
                continue
            key = row.get("canonical_game_key") or canonical_game_url(row.get("game_url", ""))
            if key:
                keys.add(key)
    return keys


def load_targets(
    input_csv: Path,
    tiers: set[int],
    name_filters: list[str],
    status_filter_keys: set[str] | None,
    max_games: int,
) -> list[TargetGame]:
    rows = list(csv.DictReader(input_csv.open(newline="", encoding="utf-8")))
    targets: list[TargetGame] = []
    for row in rows:
        game_url = row.get("game_url", "")
        game_name = row.get("game_name", "")
        if not game_url:
            continue
        tier = parse_int(row.get("followup_tier") or row.get("tier"))
        if tiers and tier not in tiers:
            continue
        canonical_key = row.get("canonical_game_key") or canonical_game_url(game_url)
        if status_filter_keys is not None and canonical_key not in status_filter_keys:
            continue
        haystack = f"{game_name} {game_url}".lower()
        if name_filters and not any(needle in haystack for needle in name_filters):
            continue
        targets.append(
            TargetGame(
                game_name=game_name,
                game_url=game_url,
                canonical_key=canonical_key,
                game_ids=tuple(
                    dict.fromkeys(
                        game_id.strip()
                        for game_id in re.split(r"[;,]\s*", row.get("kongregate_game_ids", ""))
                        if game_id.strip().isdigit()
                    )
                ),
                tier=tier,
                best_rank=parse_int(row.get("best_rank")),
                first_seen_date=row.get("first_seen_date", ""),
                last_seen_date=row.get("last_seen_date", ""),
            )
        )
        if max_games and len(targets) >= max_games:
            break
    return targets


def load_page_refs(targets: list[TargetGame]) -> dict[str, list[PageRef]]:
    target_keys = {target.canonical_key for target in targets}
    refs_by_key: dict[str, list[PageRef]] = defaultdict(list)

    for relative_path, meta in read_json(GAME_PAGE_MANIFEST, {}).items():
        key = meta.get("canonical_game_key") or canonical_game_url(meta.get("game_url", ""))
        if key not in target_keys:
            continue
        path = ROOT / relative_path
        if not path.exists() or path.stat().st_size <= 0:
            continue
        refs_by_key[key].append(
            PageRef(
                game_name=meta.get("game_name", ""),
                game_url=meta.get("game_url", ""),
                canonical_key=key,
                timestamp=meta.get("capture_timestamp", ""),
                original_url=meta.get("original_url", ""),
                relative_path=relative_path,
                page_status="parsed_count",
            )
        )

    for meta in read_json(GAME_PAGE_FAILURES, {}).values():
        key = meta.get("canonical_game_key") or canonical_game_url(meta.get("game_url", ""))
        if key not in target_keys:
            continue
        relative_path = meta.get("cached_html", "")
        if not relative_path:
            continue
        path = ROOT / relative_path
        if not path.exists() or path.stat().st_size <= 0:
            continue
        refs_by_key[key].append(
            PageRef(
                game_name=meta.get("game_name", ""),
                game_url=meta.get("game_url", ""),
                canonical_key=key,
                timestamp=meta.get("capture_timestamp", ""),
                original_url=meta.get("original_url", ""),
                relative_path=relative_path,
                page_status=meta.get("last_error", "failed"),
            )
        )

    for key, refs in list(refs_by_key.items()):
        deduped = {ref.relative_path: ref for ref in refs}
        refs_by_key[key] = list(deduped.values())
    return refs_by_key


def game_path_from_url(game_url: str) -> str:
    parsed = urllib.parse.urlsplit(game_url)
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/]+)/?$", parsed.path)
    if not match:
        return ""
    developer, slug = match.groups()
    return f"/games/{developer}/{slug}"


def canonical_key_from_endpoint(url_or_path: str) -> str:
    cleaned = js_unescape(url_or_path).strip()
    parsed = urllib.parse.urlsplit(cleaned)
    path = parsed.path or cleaned
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/?#]+)", path)
    if not match:
        return ""
    developer, slug = match.groups()
    return canonical_game_url(f"http://www.kongregate.com/games/{developer}/{slug}")


def endpoint_matches_game(url_or_path: str, game: TargetGame) -> bool:
    endpoint_key = canonical_key_from_endpoint(url_or_path)
    return not endpoint_key or endpoint_key == game.canonical_key


def extract_field_paths(markup: str) -> list[tuple[str, str]]:
    results = []
    for match in re.finditer(r'"(chat_bootstrap_url|accomplishments_bootstrap_url|holodeck_url|game_path|login_url)"\s*:\s*"([^"]+)"', markup):
        results.append((match.group(1), js_unescape(match.group(2))))
    return results


def extract_game_ids(markup: str) -> list[str]:
    patterns = [
        r'name=["\']game_id["\'][^>]*value=["\'](\d+)["\']',
        r'value=["\'](\d+)["\'][^>]*name=["\']game_id["\']',
        r'"game_id"\s*:\s*"?(\d+)"?',
        r"\bgame_id\s*[:=]\s*['\"]?(\d+)['\"]?",
        r"kongregate_game_id[\"']?\s*[:=]\s*[\"']?(\d+)",
    ]
    values: list[str] = []
    for pattern in patterns:
        values.extend(re.findall(pattern, markup, flags=re.IGNORECASE))
    return [game_id for game_id, _count in Counter(values).most_common()]


def classify_endpoint(url_or_path: str, game_path: str, game_ids: list[str]) -> str:
    parsed = urllib.parse.urlsplit(url_or_path)
    path = parsed.path or url_or_path
    low = path.lower()
    query = parsed.query.lower()
    if low.endswith("/metrics.json"):
        return "metrics_json"
    if low.endswith("/holodeck") or "/holodeck" in low:
        return "holodeck"
    if low.endswith("/chat.js"):
        return "chat_js"
    if "chat_achievements" in low:
        return "chat_achievements"
    if "recommended_games" in low and any(game_id in query or game_id in low for game_id in game_ids):
        return "recommended_games"
    if "rating" in low and any(game_id in query or game_id in low for game_id in game_ids):
        return "rating_related"
    if "comment" in low and game_path and game_path.lower() in low:
        return "comments"
    return ""


def path_to_urls(url_or_path: str, page_original_url: str) -> list[str]:
    cleaned = js_unescape(url_or_path).strip()
    if not cleaned or cleaned.startswith("#") or cleaned.startswith("javascript:"):
        return []
    cleaned = cleaned.replace("&amp;", "&")
    parsed = urllib.parse.urlsplit(cleaned)
    if parsed.scheme in {"http", "https"}:
        urls = [cleaned]
        if parsed.netloc == "www.kongregate.com":
            other_scheme = "https" if parsed.scheme == "http" else "http"
            urls.append(urllib.parse.urlunsplit((other_scheme, parsed.netloc, parsed.path, parsed.query, "")))
        return list(dict.fromkeys(urls))
    if cleaned.startswith("//"):
        return [f"http:{cleaned}", f"https:{cleaned}"]
    if cleaned.startswith("/"):
        return [
            f"http://www.kongregate.com{cleaned}",
            f"https://www.kongregate.com{cleaned}",
        ]
    if page_original_url:
        joined = urllib.parse.urljoin(page_original_url, cleaned)
        return path_to_urls(joined, "")
    return []


def endpoint_candidates_for_page(game: TargetGame, page: PageRef, max_candidates: int) -> list[EndpointCandidate]:
    path = ROOT / page.relative_path
    markup = path.read_text(errors="replace")
    game_ids = list(dict.fromkeys([*game.game_ids, *extract_game_ids(markup)]))
    field_paths = extract_field_paths(markup)
    game_paths = [game_path_from_url(game.game_url)]
    for field, value in field_paths:
        if field == "game_path" and value and endpoint_matches_game(value, game):
            game_paths.append(value)
    game_paths = [value.rstrip("/") for value in dict.fromkeys(path for path in game_paths if path)]

    raw_candidates: list[tuple[str, str, str]] = []
    for game_path in game_paths:
        generated = [
            ("metrics_json", f"{game_path}/metrics.json", "generated_from_game_path"),
            ("holodeck", f"{game_path}/holodeck", "generated_from_game_path"),
            ("chat_js", f"{game_path}/chat.js", "generated_from_game_path"),
            ("chat_achievements", f"{game_path}/chat_achievements", "generated_from_game_path"),
            ("game_path_prefix", game_path, "generated_from_game_path"),
        ]
        raw_candidates.extend(generated)
    for game_id in game_ids:
        raw_candidates.extend(
            [
                ("recommended_games", f"/recommended_games?game_id={game_id}", "generated_from_kongregate_game_id"),
                ("recommended_games", f"/recommended_games?game_id={game_id}&gamepage_pod=true", "generated_from_kongregate_game_id"),
            ]
        )
    for field, value in field_paths:
        if not endpoint_matches_game(value, game):
            continue
        source_type = classify_endpoint(value, game_paths[0] if game_paths else "", game_ids)
        if source_type:
            raw_candidates.append((source_type, value, f"holodeck_field:{field}"))

    quoted_values = re.findall(r'["\']((?:https?:)?//[^"\']+|/[^"\']+)["\']', markup)
    for value in quoted_values:
        cleaned = js_unescape(value)
        if any(part in cleaned.lower() for part in ("assets", "game_icons", "badge_icons", "flash/", ".swf", ".png", ".jpg", ".gif", ".css")):
            continue
        for game_path in game_paths or [""]:
            if not endpoint_matches_game(cleaned, game):
                continue
            source_type = classify_endpoint(cleaned, game_path, game_ids)
            if source_type:
                raw_candidates.append((source_type, cleaned, "quoted_page_url"))
                break

    candidates: list[EndpointCandidate] = []
    seen_urls: set[str] = set()
    priority = {
        "metrics_json": 0,
        "holodeck": 1,
        "chat_js": 2,
        "chat_achievements": 3,
        "game_path_prefix": 4,
        "recommended_games": 5,
        "rating_related": 6,
        "comments": 7,
    }
    raw_candidates.sort(key=lambda item: (priority.get(item[0], 99), item[1]))
    for source_type, url_or_path, discovered_from in raw_candidates:
        for endpoint_url in path_to_urls(url_or_path, page.original_url or game.game_url):
            if endpoint_url in seen_urls:
                continue
            seen_urls.add(endpoint_url)
            candidates.append(
                EndpointCandidate(
                    game=game,
                    page=page,
                    source_type=source_type,
                    endpoint_url=endpoint_url,
                    discovered_from=discovered_from,
                )
            )
            if max_candidates and len(candidates) >= max_candidates:
                return candidates
    return candidates


def endpoint_candidates_for_direct_game(game: TargetGame, max_candidates: int) -> list[EndpointCandidate]:
    page = PageRef(
        game_name=game.game_name,
        game_url=game.game_url,
        canonical_key=game.canonical_key,
        timestamp=timestamp_from_date(game.first_seen_date),
        original_url=game.game_url,
        relative_path="",
        page_status="direct_catalog_probe",
    )
    game_path = game_path_from_url(game.game_url)
    raw_candidates: list[tuple[str, str, str]] = []
    if game_path:
        raw_candidates.extend(
            [
                ("metrics_json", f"{game_path}/metrics.json", "generated_from_catalog_game_url"),
                ("holodeck", f"{game_path}/holodeck", "generated_from_catalog_game_url"),
                ("chat_js", f"{game_path}/chat.js", "generated_from_catalog_game_url"),
                ("chat_achievements", f"{game_path}/chat_achievements", "generated_from_catalog_game_url"),
                ("game_path_prefix", game_path, "generated_from_catalog_game_url"),
            ]
        )
    for game_id in game.game_ids:
        raw_candidates.extend(
            [
                ("recommended_games", f"/recommended_games?game_id={game_id}", "generated_from_kongregate_game_id"),
                ("recommended_games", f"/recommended_games?game_id={game_id}&gamepage_pod=true", "generated_from_kongregate_game_id"),
            ]
        )

    candidates: list[EndpointCandidate] = []
    seen_urls: set[str] = set()
    for source_type, url_or_path, discovered_from in raw_candidates:
        for endpoint_url in path_to_urls(url_or_path, game.game_url):
            if endpoint_url in seen_urls:
                continue
            seen_urls.add(endpoint_url)
            candidates.append(
                EndpointCandidate(
                    game=game,
                    page=page,
                    source_type=source_type,
                    endpoint_url=endpoint_url,
                    discovered_from=discovered_from,
                )
            )
            if max_candidates and len(candidates) >= max_candidates:
                return candidates
    return candidates


def cdx_cache_path(endpoint_url: str, match_type: str) -> Path:
    return RAW_CDX / f"{safe_name(match_type + '_' + endpoint_url)}_{sha(match_type + ':' + endpoint_url)}.json"


def cdx_query_url(endpoint_url: str, match_type: str, collapse: str) -> str:
    params = [
        ("url", endpoint_url),
        ("output", "json"),
        ("fl", ",".join(CDX_FIELDS)),
        ("filter", "statuscode:200"),
    ]
    if match_type:
        params.append(("matchType", match_type))
    if collapse:
        params.append(("collapse", collapse))
    return f"{CDX_ENDPOINT}?{urllib.parse.urlencode(params)}"


def fetch_cdx(
    endpoint_url: str,
    match_type: str,
    collapse: str,
    timeout_s: int,
    wall_timeout_s: float,
    refresh: bool,
    cached_only: bool,
    retries: int,
    retry_sleep_s: float,
) -> tuple[list[dict[str, str]], str]:
    RAW_CDX.mkdir(parents=True, exist_ok=True)
    cache_path = cdx_cache_path(endpoint_url, match_type)
    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text()), "cached"
    if cached_only:
        return [], "missing_cache_skipped"

    request = urllib.request.Request(
        cdx_query_url(endpoint_url, match_type, collapse),
        headers={"User-Agent": "KongregateCountSourceProbe/0.1"},
    )
    last_error = ""
    for attempt in range(retries + 1):
        try:
            with wall_clock_timeout(wall_timeout_s):
                with urllib.request.urlopen(request, timeout=timeout_s) as response:
                    data = json.loads(response.read().decode("utf-8", errors="replace"))
            break
        except (RequestWallClockTimeout, TimeoutError, socket.timeout, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            if attempt < retries:
                time.sleep(retry_sleep_s * (attempt + 1))
    else:
        ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\tcdx\t{endpoint_url}\t{last_error}\n")
        return [], f"failed: {last_error}"

    headers = data[0] if data else CDX_FIELDS
    rows = [dict(zip(headers, row)) for row in data[1:]] if len(data) > 1 else []
    cache_path.write_text(json.dumps(rows, indent=2, sort_keys=True))
    return rows, "fetched"


def payload_cache_path(timestamp: str, original: str) -> Path:
    return RAW_PAYLOADS / f"{timestamp}_{safe_name(original)}_{sha(timestamp + ':' + original)}.txt"


def decode_payload(payload: bytes, headers) -> str:
    if payload[:2] == b"\x1f\x8b" or str(headers.get("Content-Encoding", "")).lower() == "gzip":
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass
    return payload.decode("utf-8", errors="replace")


def fetch_payload(timestamp: str, original: str, timeout_s: int, wall_timeout_s: float) -> tuple[str, str, str]:
    target = payload_cache_path(timestamp, original)
    if target.exists() and target.stat().st_size > 0:
        return target.read_text(errors="replace"), relative(target), "cached"

    request = urllib.request.Request(
        WAYBACK_RAW.format(timestamp=timestamp, original=original),
        headers={"User-Agent": "KongregateCountSourceProbe/0.1", "Accept": "application/json,text/javascript,text/html,text/plain,*/*"},
    )
    try:
        with wall_clock_timeout(wall_timeout_s):
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                text = decode_payload(response.read(), response.headers)
    except urllib.error.HTTPError as exc:
        text = decode_payload(exc.read(), exc.headers)
        if exc.code >= 500:
            ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\tpayload\t{timestamp}\t{original}\thttp_{exc.code}\n")
            return "", "", f"failed: http_{exc.code}"
    except (RequestWallClockTimeout, TimeoutError, socket.timeout, urllib.error.URLError) as exc:
        ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\tpayload\t{timestamp}\t{original}\t{exc}\n")
        return "", "", f"failed: {exc}"

    if not text:
        return "", "", "empty"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return text, relative(target), "fetched"


def select_rows_near_page(rows: list[dict[str, str]], page_timestamp: str, limit: int) -> list[dict[str, str]]:
    if not limit:
        return rows
    page_value = parse_int(page_timestamp[:14])
    return sorted(rows, key=lambda row: abs(parse_int(row.get("timestamp", "")[:14]) - page_value))[:limit]


def analyze_payload(text: str) -> tuple[str, int, str]:
    if not text:
        return "", 0, ""
    patterns = [
        ("gameplays_count_with_delimiter", r"gameplays_count_with_delimiter[\"']?\s*[:=]\s*[\"']?(\d[\d,]*)"),
        ("gameplays_count", r"gameplays_count[\"']?\s*[:=]\s*[\"']?(\d[\d,]*)"),
        ("plays_count", r"plays_count[\"']?\s*[:=]\s*[\"']?(\d[\d,]*)"),
        ("favorite_game_block", r"Favorited\s+\d[\d,]*\s+times\s+(\d[\d,]*)\s+(?:gameplays|plays)\b"),
        ("plain_gameplays", r"(\d[\d,]*)\s+(?:gameplays|plays)\b"),
    ]
    for label, pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return label, parse_int(match.group(1)), ""
    terms = []
    for term in ["gameplays_count", "gameplays", "plays", "favorites_count", "favorite_message"]:
        if term.lower() in text.lower():
            terms.append(term)
    if terms:
        return "term_only", 0, ",".join(terms)
    return "", 0, ""


def write_candidates(rows: list[dict[str, object]]) -> None:
    CANDIDATES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with CANDIDATES_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def history_row_key(row: dict[str, object]) -> tuple[str, ...]:
    return tuple(str(row.get(column, "")) for column in CSV_COLUMNS)


def merge_candidate_history(rows: list[dict[str, object]], run_timestamp: str) -> dict[str, int]:
    existing_rows: list[dict[str, object]] = []
    if HISTORY_CSV.exists():
        with HISTORY_CSV.open(newline="", encoding="utf-8") as handle:
            existing_rows = list(csv.DictReader(handle))

    merged: dict[tuple[str, ...], dict[str, object]] = {}
    for row in existing_rows:
        if cdx_status_prefix(row.get("cdx_status")) == "missing_cache_skipped":
            continue
        key = history_row_key(row)
        merged[key] = {column: row.get(column, "") for column in HISTORY_COLUMNS}

    added = 0
    updated = 0
    for row in rows:
        if cdx_status_prefix(row.get("cdx_status")) == "missing_cache_skipped":
            continue
        key = history_row_key(row)
        if key not in merged:
            merged[key] = {
                "first_probe_run_timestamp": run_timestamp,
                "last_probe_run_timestamp": run_timestamp,
                "probe_seen_count": 1,
                **{column: row.get(column, "") for column in CSV_COLUMNS},
            }
            added += 1
            continue
        merged[key]["last_probe_run_timestamp"] = run_timestamp
        merged[key]["probe_seen_count"] = parse_int(merged[key].get("probe_seen_count")) + 1
        updated += 1

    output_rows = sorted(
        merged.values(),
        key=lambda row: (
            str(row.get("game_name", "")).lower(),
            str(row.get("source_type", "")),
            str(row.get("endpoint_url", "")),
            str(row.get("sample_timestamp", "")),
            str(row.get("cdx_status", "")),
        ),
    )
    HISTORY_CSV.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)
    return {"added": added, "updated": updated, "total": len(output_rows)}


def positive_count_key(row: dict[str, object]) -> tuple[str, str, str, str, int]:
    return (
        canonical_game_url(str(row.get("game_url", ""))),
        str(row.get("source_page_timestamp", "")),
        str(row.get("sample_timestamp", "")),
        str(row.get("sample_original", "")),
        parse_int(row.get("parsed_plays")),
    )


def merge_play_count_rows(rows: list[dict[str, object]]) -> dict[str, int]:
    existing_rows: list[dict[str, object]] = []
    if PLAY_COUNTS_CSV.exists():
        with PLAY_COUNTS_CSV.open(newline="", encoding="utf-8") as handle:
            existing_rows = list(csv.DictReader(handle))

    merged: dict[tuple[str, str, str, str, int], dict[str, object]] = {}
    for row in existing_rows:
        if parse_int(row.get("parsed_plays")) > 0:
            merged[positive_count_key(row)] = {column: row.get(column, "") for column in CSV_COLUMNS}

    added = 0
    for row in rows:
        if parse_int(row.get("parsed_plays")) <= 0:
            continue
        key = positive_count_key(row)
        if key in merged:
            continue
        merged[key] = {column: row.get(column, "") for column in CSV_COLUMNS}
        added += 1

    output_rows = sorted(
        merged.values(),
        key=lambda row: (
            str(row.get("game_name", "")).lower(),
            str(row.get("source_page_timestamp", "")),
            str(row.get("sample_timestamp", "")),
            str(row.get("sample_original", "")),
        ),
    )
    PLAY_COUNTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with PLAY_COUNTS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)
    return {"added": added, "total": len(output_rows)}


def make_report(args, targets: list[TargetGame], pages_by_key: dict[str, list[PageRef]], rows: list[dict[str, object]]) -> dict[str, object]:
    games_with_pages = sum(1 for target in targets if pages_by_key.get(target.canonical_key))
    games_without_pages = len(targets) - games_with_pages
    direct_probe_rows = [row for row in rows if not row.get("source_page_path")]
    games_direct_probed = len({row.get("game_url") for row in direct_probe_rows})
    games_with_ids = sum(1 for target in targets if target.game_ids)
    cdx_rows_found = sum(parse_int(row.get("cdx_rows")) for row in rows)
    rows_with_cdx = [row for row in rows if parse_int(row.get("cdx_rows")) > 0]
    rows_with_signals = [row for row in rows if row.get("count_signal")]
    rows_with_counts = [row for row in rows if parse_int(row.get("parsed_plays")) > 0]
    cdx_status_counts = Counter(cdx_status_prefix(row.get("cdx_status")) for row in rows)
    by_game: dict[str, dict[str, object]] = {}
    for target in targets:
        game_rows = [row for row in rows if row.get("game_url") == target.game_url]
        cached_page_paths = {row.get("source_page_path") for row in game_rows if row.get("source_page_path")}
        by_game[target.game_name] = {
            "game_url": target.game_url,
            "pages_checked": len(cached_page_paths),
            "direct_catalog_probe_candidates": sum(1 for row in game_rows if not row.get("source_page_path")),
            "endpoint_candidates": len(game_rows),
            "candidates_with_cdx": sum(1 for row in game_rows if parse_int(row.get("cdx_rows")) > 0),
            "payloads_with_count_signal": sum(1 for row in game_rows if row.get("count_signal")),
            "parsed_play_counts": [parse_int(row.get("parsed_plays")) for row in game_rows if parse_int(row.get("parsed_plays")) > 0],
        }
    return {
        "run_timestamp": utc_now(),
        "input_csv": relative(Path(args.input_csv)),
        "tiers": sorted(args.tiers_set),
        "game_name_contains": args.game_name_contains,
        "status_filter": args.status_filter,
        "status_csv": relative(Path(args.status_csv)),
        "target_games": len(targets),
        "target_games_with_kongregate_ids": games_with_ids,
        "games_with_cached_pages": games_with_pages,
        "games_without_cached_pages": games_without_pages,
        "games_direct_probed": games_direct_probed,
        "max_pages_per_game": args.max_pages_per_game,
        "max_candidates_per_page": args.max_candidates_per_page,
        "max_cdx_lookups": args.max_cdx_lookups,
        "stopped_after_cdx_lookup_cap": bool(getattr(args, "stopped_after_cdx_lookup_cap", False)),
        "source_types": sorted(args.source_types_set),
        "match_type": args.match_type,
        "collapse": args.collapse,
        "cdx_wall_timeout": args.cdx_wall_timeout,
        "payload_wall_timeout": args.payload_wall_timeout,
        "cached_cdx_only": args.cached_cdx_only,
        "cdx_lookups": getattr(args, "cdx_lookups_performed", len(rows)),
        "candidate_observation_rows": len(rows),
        "cdx_status_counts": dict(sorted(cdx_status_counts.items())),
        "cdx_rows_found": cdx_rows_found,
        "candidates_with_cdx": len(rows_with_cdx),
        "payloads_with_count_signal": len(rows_with_signals),
        "parsed_play_count_rows": len(rows_with_counts),
        "per_game": by_game,
        "top_candidates_with_cdx": rows_with_cdx[:50],
        "top_count_signals": rows_with_signals[:50],
        "outputs": {
            "candidate_csv": relative(CANDIDATES_CSV),
            "history_csv": relative(HISTORY_CSV),
            "play_counts_csv": relative(PLAY_COUNTS_CSV),
            "report_json": relative(REPORT_JSON),
            "report_md": relative(REPORT_MD),
        },
    }


def write_report(report: dict[str, object]) -> None:
    write_json(REPORT_JSON, report)
    signal_rows = report.get("top_count_signals", [])
    cdx_rows = report.get("top_candidates_with_cdx", [])
    lines = [
        "# Archived Count Source Probe",
        "",
        f"- Generated: {report['run_timestamp']}",
        f"- Target games: {report['target_games']}",
        f"- Status filter: {report.get('status_filter') or 'none'}",
        f"- Games with cached archived pages: {report['games_with_cached_pages']}",
        f"- Games direct-probed from catalog URLs: {report.get('games_direct_probed', 0)}",
        f"- Endpoint candidates checked: {report['cdx_lookups']}",
        f"- Candidate observation rows: {report.get('candidate_observation_rows', report['cdx_lookups'])}",
        f"- CDX status counts: {', '.join(f'{key}={value}' for key, value in report['cdx_status_counts'].items()) or 'none'}",
        f"- CDX rows found: {report['cdx_rows_found']}",
        f"- Candidates with CDX rows: {report['candidates_with_cdx']}",
        f"- Payloads with count-like signals: {report['payloads_with_count_signal']}",
        f"- Parsed play-count rows: {report['parsed_play_count_rows']}",
    ]
    persisted = report.get("persisted_play_counts", {})
    if persisted:
        lines.append(
            f"- Deduped recovered play-count observations: {persisted.get('total', 0)} ({persisted.get('added', 0)} new this run)"
        )
    history = report.get("persisted_probe_history", {})
    if history:
        lines.append(
            f"- Accumulated probe-history rows: {history.get('total', 0)} ({history.get('added', 0)} new, {history.get('updated', 0)} refreshed)"
        )
    if report.get("stopped_after_cdx_lookup_cap"):
        lines.append(f"- Stopped after CDX lookup cap: {report.get('max_cdx_lookups', 0)}")
    lines.append("")
    if signal_rows:
        lines.extend(["## Count Signals", "", "| Game | Source | Endpoint | Sample | Signal | Plays |", "| --- | --- | --- | --- | --- | --- |"])
        for row in signal_rows[:20]:
            plays_value = row["parsed_plays"] or "n/a"
            lines.append(
                f"| {row['game_name']} | {row['source_type']} | `{row['endpoint_url']}` | `{row.get('sample_original', '')}` | {row['count_signal']} | {plays_value} |"
            )
        lines.append("")
    if cdx_rows:
        lines.extend(["## Archived Endpoint Hits", "", "| Game | Source | Endpoint | Sample | CDX rows |", "| --- | --- | --- | --- | ---: |"])
        for row in cdx_rows[:20]:
            lines.append(f"| {row['game_name']} | {row['source_type']} | `{row['endpoint_url']}` | `{row.get('sample_original', '')}` | {row['cdx_rows']} |")
        lines.append("")
    parsed_count_rows = parse_int(report.get("parsed_play_count_rows"))
    failed_count = parse_int(report.get("cdx_status_counts", {}).get("failed"))
    if signal_rows and not parsed_count_rows:
        lines.extend(
            [
                "## Interpretation",
                "",
                "The only count-like terms sampled here were non-public placeholders or guest/user counters, not numeric game play totals. No endpoint payload in this run produced a trusted play-count observation.",
                "",
            ]
        )
    elif not signal_rows:
        lines.extend(
            [
                "## Interpretation",
                "",
                "No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.",
                "",
            ]
        )
    if failed_count:
        lines.extend(
            [
                "## Retry Note",
                "",
                f"{failed_count} CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.",
                "",
            ]
        )
    lines.extend(
        [
            "## Output Files",
            "",
            f"- `{report['outputs']['candidate_csv']}`",
            f"- `{report['outputs']['history_csv']}`",
            f"- `{report['outputs']['play_counts_csv']}`",
            f"- `{report['outputs']['report_json']}`",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe archived game-page side endpoints for Kongregate play-count recovery.")
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT_CSV), help="CSV with game_name and game_url columns.")
    parser.add_argument("--tiers", default="1,2", help="Comma-separated follow-up tiers to target when present. Empty means all.")
    parser.add_argument("--game-name-contains", default="", help="Comma-separated case-insensitive substrings to target by game name or URL.")
    parser.add_argument("--status-filter", default="", help="Comma-separated values from count_source_probe_game_status.csv to target, e.g. not_probed or transient_failures_remaining.")
    parser.add_argument("--status-csv", default=str(GAME_STATUS_CSV), help="Probe status CSV used with --status-filter.")
    parser.add_argument("--max-games", type=int, default=0, help="Limit target games after filtering. 0 means no limit.")
    parser.add_argument("--max-pages-per-game", type=int, default=2, help="Cached archived pages to inspect per game.")
    parser.add_argument("--max-candidates-per-page", type=int, default=12, help="Endpoint candidates to query per cached page.")
    parser.add_argument("--source-types", default="", help="Comma-separated endpoint source types to include, e.g. metrics_json, recommended_games, game_path_prefix. Empty means all.")
    parser.add_argument("--match-type", default="exact", choices=["exact", "prefix"], help="CDX match type for candidate endpoints.")
    parser.add_argument("--collapse", default="digest", help="Optional CDX collapse value.")
    parser.add_argument("--timeout", type=int, default=12, help="Per-request timeout in seconds.")
    parser.add_argument("--cdx-wall-timeout", type=float, default=0, help="Optional wall-clock cap for each CDX lookup, including slow redirects/reads.")
    parser.add_argument("--payload-wall-timeout", type=float, default=0, help="Optional wall-clock cap for each archived endpoint payload fetch.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Seconds to sleep after fresh network requests.")
    parser.add_argument("--cdx-retries", type=int, default=1, help="Retries for transient CDX lookup failures.")
    parser.add_argument("--retry-sleep", type=float, default=1.0, help="Initial seconds to back off between CDX retries.")
    parser.add_argument("--max-samples-per-candidate", type=int, default=1, help="Archived endpoint payloads to inspect per candidate.")
    parser.add_argument("--max-fetches", type=int, default=40, help="Total archived endpoint payload fetches to inspect. 0 means none.")
    parser.add_argument("--max-cdx-lookups", type=int, default=0, help="Total endpoint CDX lookups to perform. 0 means no cap.")
    parser.add_argument("--refresh-cdx", action="store_true", help="Refresh cached CDX responses.")
    parser.add_argument("--cached-cdx-only", action="store_true", help="Use only existing CDX cache files.")
    args = parser.parse_args()
    args.tiers_set = {parse_int(value) for value in args.tiers.split(",") if value.strip()}
    args.source_types_set = set(csv_list(args.source_types))
    args.status_filter_set = {value.lower() for value in csv_list(args.status_filter)}

    for directory in (RAW_CDX, RAW_PAYLOADS, PROCESSED, LOGS):
        directory.mkdir(parents=True, exist_ok=True)

    name_filters = [value.lower() for value in csv_list(args.game_name_contains)]
    status_filter_keys = load_status_filter_keys(Path(args.status_csv), args.status_filter_set)
    targets = load_targets(Path(args.input_csv), args.tiers_set, name_filters, status_filter_keys, args.max_games)
    pages_by_key = load_page_refs(targets)
    candidate_rows: list[dict[str, object]] = []
    payload_fetches = 0
    cdx_lookups = 0
    stopped_after_cdx_lookup_cap = False

    for game in targets:
        if stopped_after_cdx_lookup_cap:
            break
        page_refs = sorted(
            pages_by_key.get(game.canonical_key, []),
            key=lambda page: (page_distance(game, page), page.timestamp, page.relative_path),
        )
        if args.max_pages_per_game:
            page_refs = page_refs[: args.max_pages_per_game]
        generation_candidate_limit = 0 if args.source_types_set else args.max_candidates_per_page
        candidate_batches = (
            [endpoint_candidates_for_page(game, page, generation_candidate_limit) for page in page_refs]
            if page_refs
            else [endpoint_candidates_for_direct_game(game, generation_candidate_limit)]
        )
        for candidates in candidate_batches:
            if stopped_after_cdx_lookup_cap:
                break
            accepted_candidates = 0
            for candidate in candidates:
                page = candidate.page
                if args.source_types_set and candidate.source_type not in args.source_types_set:
                    continue
                if args.max_candidates_per_page and accepted_candidates >= args.max_candidates_per_page:
                    break
                accepted_candidates += 1
                if args.max_cdx_lookups and cdx_lookups >= args.max_cdx_lookups:
                    stopped_after_cdx_lookup_cap = True
                    break
                cdx_lookups += 1
                rows, status = fetch_cdx(
                    candidate.endpoint_url,
                    args.match_type,
                    args.collapse,
                    args.timeout,
                    args.cdx_wall_timeout,
                    args.refresh_cdx,
                    args.cached_cdx_only,
                    args.cdx_retries,
                    args.retry_sleep,
                )
                if status not in {"cached", "missing_cache_skipped"}:
                    time.sleep(args.sleep)
                selected_rows = select_rows_near_page(rows, page.timestamp, args.max_samples_per_candidate)
                if not selected_rows:
                    candidate_rows.append(
                        {
                            "game_name": game.game_name,
                            "game_url": game.game_url,
                            "source_page_timestamp": page.timestamp,
                            "source_page_path": page.relative_path,
                            "source_type": candidate.source_type,
                            "endpoint_url": candidate.endpoint_url,
                            "cdx_status": status,
                            "cdx_rows": len(rows),
                            "sample_timestamp": "",
                            "sample_original": "",
                            "sample_mimetype": "",
                            "sample_path": "",
                            "count_signal": "",
                            "parsed_plays": "",
                            "notes": candidate.discovered_from,
                        }
                    )
                    continue

                for row in selected_rows:
                    signal = ""
                    parsed_plays = 0
                    notes = candidate.discovered_from
                    sample_path = ""
                    if args.max_fetches and payload_fetches < args.max_fetches:
                        text, sample_path, fetch_status = fetch_payload(
                            row.get("timestamp", ""),
                            row.get("original", ""),
                            args.timeout,
                            args.payload_wall_timeout,
                        )
                        payload_fetches += 1
                        if fetch_status not in {"cached"}:
                            time.sleep(args.sleep)
                        signal, parsed_plays, term_notes = analyze_payload(text)
                        notes = ",".join(part for part in [notes, fetch_status, term_notes] if part)
                    candidate_rows.append(
                        {
                            "game_name": game.game_name,
                            "game_url": game.game_url,
                            "source_page_timestamp": page.timestamp,
                            "source_page_path": page.relative_path,
                            "source_type": candidate.source_type,
                            "endpoint_url": candidate.endpoint_url,
                            "cdx_status": status,
                            "cdx_rows": len(rows),
                            "sample_timestamp": row.get("timestamp", ""),
                            "sample_original": row.get("original", ""),
                            "sample_mimetype": row.get("mimetype", ""),
                            "sample_path": sample_path,
                            "count_signal": signal,
                            "parsed_plays": parsed_plays or "",
                            "notes": notes,
                        }
                    )

    candidate_rows.sort(
        key=lambda row: (
            0 if row.get("count_signal") else 1,
            -parse_int(row.get("parsed_plays")),
            -parse_int(row.get("cdx_rows")),
            str(row.get("game_name", "")).lower(),
            str(row.get("source_type", "")),
            str(row.get("endpoint_url", "")),
        )
    )
    write_candidates(candidate_rows)
    run_timestamp = utc_now()
    history_merge = merge_candidate_history(candidate_rows, run_timestamp)
    play_count_merge = merge_play_count_rows(candidate_rows)
    args.cdx_lookups_performed = cdx_lookups
    args.stopped_after_cdx_lookup_cap = stopped_after_cdx_lookup_cap
    report = make_report(args, targets, pages_by_key, candidate_rows)
    report["run_timestamp"] = run_timestamp
    report["persisted_probe_history"] = history_merge
    report["persisted_play_counts"] = play_count_merge
    write_report(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
