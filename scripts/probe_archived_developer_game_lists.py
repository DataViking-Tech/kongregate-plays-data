#!/usr/bin/env python3
"""Probe archived developer game-list pages for per-game play counts."""

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
from probe_archived_count_sources import (
    CSV_COLUMNS,
    HISTORY_COLUMNS,
    cdx_status_prefix,
    merge_candidate_history,
    merge_play_count_rows,
    parse_int,
)


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_DEV_LISTS = ROOT / "data" / "raw" / "developer_game_lists"
RAW_CDX = RAW_DEV_LISTS / "cdx"
RAW_HTML = RAW_DEV_LISTS / "html"
LOGS = ROOT / "logs"

DEFAULT_INPUT_CSV = PROCESSED / "metrics_no_cdx_profile.csv"
CURRENT_CSV = PROCESSED / "developer_game_list_probe_candidates.csv"
HISTORY_CSV = PROCESSED / "count_source_probe_history.csv"
REPORT_JSON = LOGS / "developer_game_list_probe_report.json"
REPORT_MD = LOGS / "developer_game_list_probe_report.md"
ERROR_LOG = LOGS / "developer_game_list_probe_errors.log"

CDX_ENDPOINT = "https://web.archive.org/cdx"
WAYBACK_RAW = "https://web.archive.org/web/{timestamp}id_/{original}"
CDX_FIELDS = ["timestamp", "original", "statuscode", "mimetype", "digest", "length"]

GAME_HREF_RE = re.compile(
    r"""href=["'](?P<href>(?:https?:)?//(?:www\.)?kongregate\.com/games/[^"']+|/(?:en/)?games/[^"']+)["']""",
    re.IGNORECASE,
)
PLAY_TEXT_RE = re.compile(r"\b(\d[\d,]*(?:\.\d+)?)\s*([kmb])?\s+(plays|gameplays)\b", re.IGNORECASE)


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
    developer: str
    slug: str
    tier: int
    best_rank: int
    first_seen_date: str
    last_seen_date: str


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def developer_source_identity(source_url: str) -> str:
    parsed = urllib.parse.urlsplit(source_url or "")
    path = urllib.parse.unquote(parsed.path).rstrip("/") or "/"
    query = f"?{parsed.query.lower()}" if parsed.query else ""
    return f"{path.lower()}{query}"


def unresolved_failed_developer_endpoint_filter(history_csv: Path) -> set[tuple[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(history_csv):
        if row.get("source_type") != "developer_game_list":
            continue
        key = (canonical_game_url(row.get("game_url", "")), developer_source_identity(row.get("endpoint_url", "")))
        if not key[0] or not key[1]:
            continue
        grouped[key].append(row)

    retry_keys: set[tuple[str, str]] = set()
    for key, rows in grouped.items():
        has_failure = any(cdx_status_prefix(row.get("cdx_status")) == "failed" for row in rows)
        has_successful_retry = any(cdx_status_prefix(row.get("cdx_status")) in {"cached", "fetched"} for row in rows)
        if has_failure and not has_successful_retry:
            retry_keys.add(key)
    return retry_keys


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def game_url_parts(game_url: str) -> tuple[str, str] | None:
    parsed = urllib.parse.urlsplit(game_url or "")
    match = re.match(r"^/(?:en/)?games/([^/]+)/([^/?#]+)", parsed.path)
    if not match:
        return None
    return urllib.parse.unquote(match.group(1)), urllib.parse.unquote(match.group(2))


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


def capture_distance(row: dict[str, str], targets: list[TargetGame]) -> int:
    capture_date = parse_timestamp_date(row.get("timestamp", ""))
    if not capture_date:
        return 0
    distances = []
    for target in targets:
        first_seen = parse_date(target.first_seen_date)
        last_seen = parse_date(target.last_seen_date) or first_seen
        if not first_seen:
            continue
        if first_seen <= capture_date <= last_seen:
            return 0
        distances.append(min(abs((capture_date - first_seen).days), abs((capture_date - last_seen).days)))
    return min(distances) if distances else 0


def load_targets(args) -> list[TargetGame]:
    tiers = {parse_int(part) for part in str(args.tiers or "").split(",") if part.strip()}
    name_filters = [value.lower() for value in args.game_name_contains]
    developer_filters = {value.lower() for value in args.developer}
    rows = read_csv(Path(args.input_csv))
    targets: list[TargetGame] = []
    for row in rows:
        game_url = row.get("game_url", "")
        parts = game_url_parts(game_url)
        if not parts:
            continue
        developer, slug = parts
        tier = parse_int(row.get("followup_tier") or row.get("tier"))
        if tiers and tier not in tiers:
            continue
        if developer_filters and developer.lower() not in developer_filters:
            continue
        haystack = f"{row.get('game_name', '')} {game_url}".lower()
        if name_filters and not any(needle in haystack for needle in name_filters):
            continue
        targets.append(
            TargetGame(
                game_name=row.get("game_name", ""),
                game_url=game_url,
                canonical_key=row.get("canonical_game_key") or canonical_game_url(game_url),
                developer=developer,
                slug=slug,
                tier=tier,
                best_rank=parse_int(row.get("best_rank")),
                first_seen_date=row.get("first_seen_date", ""),
                last_seen_date=row.get("last_seen_date", ""),
            )
        )
    targets.sort(key=lambda target: (target.tier or 99, target.best_rank or 999999, target.first_seen_date, target.game_name.lower()))
    args.pre_cap_target_games = len(targets)
    args.pre_cap_target_developers = len({target.developer for target in targets})
    args.pre_cap_games_by_developer = dict(sorted(Counter(target.developer for target in targets).items()))
    if args.max_games_per_developer:
        capped_targets: list[TargetGame] = []
        games_by_developer: Counter[str] = Counter()
        for target in targets:
            if games_by_developer[target.developer] >= args.max_games_per_developer:
                continue
            capped_targets.append(target)
            games_by_developer[target.developer] += 1
        targets = capped_targets
    if args.max_games:
        targets = targets[: args.max_games]
    args.selected_games_by_developer = dict(sorted(Counter(target.developer for target in targets).items()))
    selected_developers = set(args.selected_games_by_developer)
    args.skipped_developers_due_to_caps = [
        developer for developer in sorted(args.pre_cap_games_by_developer) if developer not in selected_developers
    ]
    return targets


def developer_source_urls(developer: str, include_account_pages: bool = False) -> list[str]:
    quoted = urllib.parse.quote(developer, safe="")
    urls = [
        f"http://www.kongregate.com/games/{quoted}",
        f"http://www.kongregate.com:80/games/{quoted}",
        f"https://www.kongregate.com/games/{quoted}",
    ]
    if include_account_pages:
        urls.extend(
            [
                f"http://www.kongregate.com/accounts/{quoted}",
                f"http://www.kongregate.com:80/accounts/{quoted}",
                f"https://www.kongregate.com/accounts/{quoted}",
                f"http://www.kongregate.com/accounts/{quoted}/games",
                f"http://www.kongregate.com:80/accounts/{quoted}/games",
                f"https://www.kongregate.com/accounts/{quoted}/games",
            ]
        )
    return urls


def cdx_cache_path(source_url: str, match_type: str) -> Path:
    return RAW_CDX / f"{safe_name(match_type + '_' + source_url)}_{sha(match_type + ':' + source_url)}.json"


def cdx_query_url(source_url: str, match_type: str, collapse: str) -> str:
    params = [
        ("url", source_url),
        ("output", "json"),
        ("fl", ",".join(CDX_FIELDS)),
        ("filter", "statuscode:200"),
    ]
    if match_type:
        params.append(("matchType", match_type))
    if collapse:
        params.append(("collapse", collapse))
    return f"{CDX_ENDPOINT}?{urllib.parse.urlencode(params)}"


def fetch_cdx(source_url: str, args) -> tuple[list[dict[str, str]], str]:
    RAW_CDX.mkdir(parents=True, exist_ok=True)
    cache_path = cdx_cache_path(source_url, args.match_type)
    if cache_path.exists() and not args.refresh_cdx:
        return json.loads(cache_path.read_text()), "cached"
    if args.cached_cdx_only:
        return [], "missing_cache_skipped"

    request = urllib.request.Request(
        cdx_query_url(source_url, args.match_type, args.collapse),
        headers={"User-Agent": "KongregateDeveloperListProbe/0.1"},
    )
    last_error = ""
    for attempt in range(args.retries + 1):
        try:
            with wall_clock_timeout(args.cdx_wall_timeout):
                with urllib.request.urlopen(request, timeout=args.timeout) as response:
                    data = json.loads(response.read().decode("utf-8", errors="replace"))
            break
        except (RequestWallClockTimeout, TimeoutError, socket.timeout, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            if attempt < args.retries:
                time.sleep(args.retry_sleep * (attempt + 1))
    else:
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\tcdx\t{source_url}\t{last_error}\n")
        return [], f"failed: {last_error}"

    headers = data[0] if data else CDX_FIELDS
    rows = [dict(zip(headers, row)) for row in data[1:]] if len(data) > 1 else []
    cache_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    return rows, "fetched"


def is_source_original(original: str, source_url: str) -> bool:
    parsed = urllib.parse.urlsplit(original or "")
    source = urllib.parse.urlsplit(source_url or "")
    path = urllib.parse.unquote(parsed.path).rstrip("/") or "/"
    source_path = urllib.parse.unquote(source.path).rstrip("/") or "/"
    return path == source_path


def html_cache_path(timestamp: str, original: str) -> Path:
    return RAW_HTML / f"{timestamp}_{safe_name(original)}_{sha(timestamp + ':' + original)}.html"


def decode_payload(payload: bytes, headers) -> str:
    if payload[:2] == b"\x1f\x8b" or str(headers.get("Content-Encoding", "")).lower() == "gzip":
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass
    return payload.decode("utf-8", errors="replace")


def fetch_html(timestamp: str, original: str, args) -> tuple[str, str, str]:
    target = html_cache_path(timestamp, original)
    if target.exists() and target.stat().st_size > 0 and not args.refresh_html:
        return target.read_text(errors="replace"), relative(target), "cached"
    if args.cached_html_only:
        return "", "", "missing_html_cache_skipped"

    request = urllib.request.Request(
        WAYBACK_RAW.format(timestamp=timestamp, original=original),
        headers={"User-Agent": "KongregateDeveloperListProbe/0.1", "Accept": "text/html,*/*"},
    )
    try:
        with wall_clock_timeout(args.payload_wall_timeout):
            with urllib.request.urlopen(request, timeout=args.timeout) as response:
                text = decode_payload(response.read(), response.headers)
    except urllib.error.HTTPError as exc:
        text = decode_payload(exc.read(), exc.headers)
        if exc.code >= 500:
            ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
            ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\thtml\t{timestamp}\t{original}\thttp_{exc.code}\n")
            return "", "", f"failed: http_{exc.code}"
    except (RequestWallClockTimeout, TimeoutError, socket.timeout, urllib.error.URLError) as exc:
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        ERROR_LOG.open("a", encoding="utf-8").write(f"{utc_now()}\thtml\t{timestamp}\t{original}\t{exc}\n")
        return "", "", f"failed: {exc}"

    if not text:
        return "", "", "empty"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return text, relative(target), "fetched"


def strip_markup(markup: str) -> str:
    markup = re.sub(r"<script\b.*?</script>", " ", markup, flags=re.IGNORECASE | re.DOTALL)
    markup = re.sub(r"<style\b.*?</style>", " ", markup, flags=re.IGNORECASE | re.DOTALL)
    markup = re.sub(r"<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(markup)).strip()


def game_key_from_href(href: str) -> str:
    cleaned = html.unescape(href).replace("\\/", "/")
    if cleaned.startswith("//"):
        cleaned = f"http:{cleaned}"
    elif cleaned.startswith("/"):
        cleaned = f"http://www.kongregate.com{cleaned}"
    return canonical_game_url(cleaned)


def visible_play_count(chunk: str) -> tuple[int, str]:
    text = strip_markup(chunk)
    for match in PLAY_TEXT_RE.finditer(text):
        value = float(match.group(1).replace(",", ""))
        suffix = (match.group(2) or "").lower()
        multiplier = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}.get(suffix, 1)
        plays = int(round(value * multiplier))
        if plays > 0:
            return plays, match.group(0)
    return 0, ""


def listing_chunks(markup: str) -> list[str]:
    starts = [match.start() for match in re.finditer(r"<div\b[^>]*class=[\"'][^\"']*\bcallout_listing\b", markup, flags=re.IGNORECASE)]
    if not starts:
        return []
    starts.append(len(markup))
    return [markup[starts[index] : starts[index + 1]] for index in range(len(starts) - 1)]


def fallback_link_windows(markup: str) -> list[str]:
    windows = []
    for match in GAME_HREF_RE.finditer(markup):
        start = max(0, match.start() - 500)
        end = min(len(markup), match.end() + 1200)
        windows.append(markup[start:end])
    return windows


def parse_developer_page(markup: str, targets_by_key: dict[str, TargetGame]) -> tuple[dict[str, tuple[int, str]], set[str]]:
    counts: dict[str, tuple[int, str]] = {}
    found_keys: set[str] = set()
    chunks = listing_chunks(markup) or fallback_link_windows(markup)
    for chunk in chunks:
        keys = []
        for match in GAME_HREF_RE.finditer(chunk):
            key = game_key_from_href(match.group("href"))
            if key in targets_by_key and key not in keys:
                keys.append(key)
        if not keys:
            continue
        found_keys.update(keys)
        plays, plays_text = visible_play_count(chunk)
        if not plays:
            continue
        for key in keys:
            counts.setdefault(key, (plays, plays_text))
    return counts, found_keys


def candidate_row(
    target: TargetGame,
    source_url: str,
    cdx_status: str,
    cdx_rows: int,
    sample_timestamp: str = "",
    sample_original: str = "",
    sample_mimetype: str = "",
    sample_path: str = "",
    parsed_plays: int = 0,
    count_signal: str = "",
    notes: str = "",
) -> dict[str, object]:
    return {
        "game_name": target.game_name,
        "game_url": target.game_url,
        "source_page_timestamp": sample_timestamp,
        "source_page_path": sample_path,
        "source_type": "developer_game_list",
        "endpoint_url": source_url,
        "cdx_status": cdx_status,
        "cdx_rows": cdx_rows,
        "sample_timestamp": sample_timestamp,
        "sample_original": sample_original,
        "sample_mimetype": sample_mimetype,
        "sample_path": sample_path,
        "count_signal": count_signal,
        "parsed_plays": parsed_plays or "",
        "notes": notes,
    }


def write_current_rows(rows: list[dict[str, object]]) -> None:
    CURRENT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with CURRENT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in CSV_COLUMNS} for row in rows)


def write_report(report: dict[str, object]) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Archived Developer Game-List Probe",
        "",
        f"- Generated: {report['run_timestamp']}",
        f"- Target games: {report['target_games']}",
        f"- Target developers: {report['target_developers']}",
        f"- Source URL CDX lookups: {report['source_cdx_lookups']}",
        f"- Developer-page captures sampled: {report['captures_sampled']}",
        f"- Candidate observation rows: {report['candidate_observation_rows']}",
        f"- CDX status counts: {', '.join(f'{key}={value}' for key, value in report['cdx_status_counts'].items()) or 'none'}",
        f"- Target links found in sampled pages: {report['target_links_found']}",
        f"- Recovered play-count rows in this run: {report['parsed_play_count_rows']}",
    ]
    persisted = report.get("persisted_play_counts", {})
    if persisted:
        lines.append(f"- Deduped recovered play-count observations: {persisted.get('total', 0)} ({persisted.get('added', 0)} new this run)")
    history = report.get("persisted_probe_history", {})
    if history:
        lines.append(f"- Accumulated probe-history rows: {history.get('total', 0)} ({history.get('added', 0)} new, {history.get('updated', 0)} refreshed)")
    lines.extend(["", "## Outputs", ""])
    for key, value in report["outputs"].items():
        lines.append(f"- `{value}`")
    recovered = [row for row in report.get("top_recovered_rows", []) if parse_int(row.get("parsed_plays")) > 0]
    if recovered:
        lines.extend(["", "## Recovered Rows", "", "| Game | Plays | Capture | Source |", "| --- | ---: | --- | --- |"])
        for row in recovered[:20]:
            lines.append(f"| {row['game_name']} | {int(row['parsed_plays']):,} | {row['sample_timestamp']} | `{row['sample_original']}` |")
    if not recovered:
        lines.extend(
            [
                "",
                "## Interpretation",
                "",
                "This run did not recover new play-count rows from sampled developer game-list pages. Pages with target links either omitted visible count text or were unavailable in the sampled archived captures.",
            ]
        )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_probe(args) -> dict[str, object]:
    targets = load_targets(args)
    failed_endpoint_filter = unresolved_failed_developer_endpoint_filter(HISTORY_CSV) if args.unresolved_failed_endpoints_only else None
    targets_by_developer: dict[str, list[TargetGame]] = defaultdict(list)
    for target in targets:
        targets_by_developer[target.developer].append(target)
    if args.max_developers:
        selected_developers = list(targets_by_developer)[: args.max_developers]
        targets_by_developer = {developer: targets_by_developer[developer] for developer in selected_developers}
        targets = [target for developer in selected_developers for target in targets_by_developer[developer]]
    selected_games_by_developer = dict(sorted(Counter(target.developer for target in targets).items()))
    selected_developers = set(selected_games_by_developer)
    skipped_developers_due_to_caps = [
        developer
        for developer in sorted(getattr(args, "pre_cap_games_by_developer", {}))
        if developer not in selected_developers
    ]

    all_rows: list[dict[str, object]] = []
    source_cdx_lookups = 0
    captures_sampled = 0
    target_links_found = 0

    for developer, developer_targets in targets_by_developer.items():
        for source_url in developer_source_urls(developer, args.include_account_pages):
            source_targets = developer_targets
            if failed_endpoint_filter is not None:
                source_identity = developer_source_identity(source_url)
                source_targets = [
                    target for target in developer_targets if (target.canonical_key, source_identity) in failed_endpoint_filter
                ]
                if not source_targets:
                    continue
            target_by_key = {target.canonical_key: target for target in source_targets}
            if args.max_cdx_lookups and source_cdx_lookups >= args.max_cdx_lookups:
                args.stopped_after_cdx_lookup_cap = True
                break
            cdx_rows, cdx_status = fetch_cdx(source_url, args)
            source_cdx_lookups += 1
            if args.match_type == "prefix":
                cdx_rows = [row for row in cdx_rows if is_source_original(row.get("original", ""), source_url)]
            if not cdx_rows:
                for target in source_targets:
                    all_rows.append(
                        candidate_row(
                            target,
                            source_url,
                            cdx_status,
                            0,
                            notes="developer_game_list_cdx_no_rows",
                        )
                    )
                continue

            selected_rows = sorted(cdx_rows, key=lambda row: (capture_distance(row, source_targets), row.get("timestamp", "")))
            if args.max_captures_per_source:
                selected_rows = selected_rows[: args.max_captures_per_source]
            for cdx_row in selected_rows:
                timestamp = cdx_row.get("timestamp", "")
                original = cdx_row.get("original", source_url)
                text, sample_path, html_status = fetch_html(timestamp, original, args)
                captures_sampled += 1
                if not text:
                    for target in source_targets:
                        all_rows.append(
                            candidate_row(
                                target,
                                source_url,
                                cdx_status,
                                len(cdx_rows),
                                sample_timestamp=timestamp,
                                sample_original=original,
                                sample_mimetype=cdx_row.get("mimetype", ""),
                                notes=f"developer_game_list_html_unavailable; html_status={html_status}",
                            )
                        )
                    continue

                counts, found_keys = parse_developer_page(text, target_by_key)
                target_links_found += len(found_keys)
                for target in source_targets:
                    plays = 0
                    plays_text = ""
                    if target.canonical_key in counts:
                        plays, plays_text = counts[target.canonical_key]
                    if plays:
                        signal = "developer_game_list_play_text"
                        notes = f"developer_page_status={html_status}; play_text={plays_text}"
                    elif target.canonical_key in found_keys:
                        signal = ""
                        notes = f"developer_page_status={html_status}; target_found_without_play_count"
                    else:
                        signal = ""
                        notes = f"developer_page_status={html_status}; target_not_found_in_sample"
                    all_rows.append(
                        candidate_row(
                            target,
                            source_url,
                            cdx_status,
                            len(cdx_rows),
                            sample_timestamp=timestamp,
                            sample_original=original,
                            sample_mimetype=cdx_row.get("mimetype", ""),
                            sample_path=sample_path,
                            parsed_plays=plays,
                            count_signal=signal,
                            notes=notes,
                        )
                    )
        if getattr(args, "stopped_after_cdx_lookup_cap", False):
            break

    write_current_rows(all_rows)
    history_result = merge_candidate_history(all_rows, utc_now()) if not args.no_persist else {}
    play_result = merge_play_count_rows(all_rows) if not args.no_persist else {}

    cdx_status_counts = Counter(cdx_status_prefix(row.get("cdx_status")) for row in all_rows)
    recovered_rows = [row for row in all_rows if parse_int(row.get("parsed_plays")) > 0]
    report = {
        "run_timestamp": utc_now(),
        "input_csv": relative(Path(args.input_csv)),
        "tiers": args.tiers,
        "game_name_contains": args.game_name_contains,
        "developer_filters": args.developer,
        "target_games": len(targets),
        "target_developers": len(targets_by_developer),
        "pre_cap_target_games": getattr(args, "pre_cap_target_games", len(targets)),
        "pre_cap_target_developers": getattr(args, "pre_cap_target_developers", len(targets_by_developer)),
        "selected_games_by_developer": selected_games_by_developer,
        "skipped_developers_due_to_caps": skipped_developers_due_to_caps,
        "max_games": args.max_games,
        "max_games_per_developer": args.max_games_per_developer,
        "max_developers": args.max_developers,
        "max_cdx_lookups": args.max_cdx_lookups,
        "max_captures_per_source": args.max_captures_per_source,
        "match_type": args.match_type,
        "include_account_pages": args.include_account_pages,
        "unresolved_failed_endpoints_only": args.unresolved_failed_endpoints_only,
        "source_cdx_lookups": source_cdx_lookups,
        "captures_sampled": captures_sampled,
        "stopped_after_cdx_lookup_cap": bool(getattr(args, "stopped_after_cdx_lookup_cap", False)),
        "candidate_observation_rows": len(all_rows),
        "cdx_status_counts": dict(sorted(cdx_status_counts.items())),
        "target_links_found": target_links_found,
        "parsed_play_count_rows": len(recovered_rows),
        "persisted_probe_history": history_result,
        "persisted_play_counts": play_result,
        "top_recovered_rows": recovered_rows[:50],
        "outputs": {
            "current_csv": relative(CURRENT_CSV),
            "count_source_history_csv": "data/processed/count_source_probe_history.csv",
            "count_source_play_counts_csv": "data/processed/count_source_play_counts.csv",
            "report_json": relative(REPORT_JSON),
            "report_md": relative(REPORT_MD),
        },
    }
    write_report(report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT_CSV))
    parser.add_argument("--tiers", default="1,2,3")
    parser.add_argument("--game-name-contains", action="append", default=[])
    parser.add_argument("--developer", action="append", default=[])
    parser.add_argument("--max-games", type=int, default=12)
    parser.add_argument("--max-games-per-developer", type=int, default=0)
    parser.add_argument("--max-developers", type=int, default=0)
    parser.add_argument("--max-cdx-lookups", type=int, default=0)
    parser.add_argument("--max-captures-per-source", type=int, default=2)
    parser.add_argument("--match-type", choices=["", "exact", "prefix"], default="exact")
    parser.add_argument("--include-account-pages", action="store_true")
    parser.add_argument("--unresolved-failed-endpoints-only", action="store_true")
    parser.add_argument("--collapse", default="digest")
    parser.add_argument("--cached-cdx-only", action="store_true")
    parser.add_argument("--cached-html-only", action="store_true")
    parser.add_argument("--refresh-cdx", action="store_true")
    parser.add_argument("--refresh-html", action="store_true")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--cdx-wall-timeout", type=float, default=25)
    parser.add_argument("--payload-wall-timeout", type=float, default=25)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--retry-sleep", type=float, default=1.5)
    parser.add_argument("--no-persist", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_probe(args)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
