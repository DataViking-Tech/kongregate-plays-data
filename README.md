# Kongregate Plays Data

In-progress public dataset of Kongregate game rankings and observed play counts from archived Kongregate pages and per-game Wayback `metrics.json` captures.

Live chart:

https://dataviking-tech.github.io/kongregate-plays-data/

The live chart fetches `outputs/kongregate_ranked_games/play_count_bar_chart_race_data.json` from this repo at runtime. The Google Sheet is a companion workbook link, not the chart's live data source.

Current Google Sheet workbook:

https://docs.google.com/spreadsheets/d/1NeN3WR_qNommOPW0wphly-PWhOBiYZvDnZ7LFb9fh7Q

## Current Snapshot

- Ranked-list rows: 47,186
- Ranked-list rows with observed play counts: 14,518
- Mini catalog: 2,936 canonical games that reached top 20 in observed rankings
- Per-game metrics history rows: 7,097 across 2,569 canonical games
- Observed play-count rows used by the chart: 21,615
- Chart playback: Smooth mode uses 3,729 interpolated month-paced display frames by default; Captures mode exposes all 2,110 observed capture-date frames.
- Ranked-list date range: 2007-01-20 to 2026-06-26
- Metrics-history date range: 2013-09-18 to 2026-06-30

This scrape is still being expanded. The processed files are coherent snapshots, but coverage is not final.

## Current QA Focus

- Ranked-list freshness is current through the newest recovered Wayback rows as of 2026-06-30.
- 0 cached HTML captures remain empty or corrupted in the ranked-page cache.
- Ranked-page, homepage-fallback, and modern-frame recovery brought the HTML manifest to 3,337 cached entries with 7,608 known ranked-page failures and 742 known modern-frame failures still recorded.
- Recovery checkpoints have filled all previously empty ranked months; no calendar month from the first ranked capture through the latest ranked capture is empty in the processed dataset.
- Checkpoint 30 merged 525 raw URL-split mini-catalog identities into canonical games, retained the raw forms in `game_url_variants`, and duplicate canonical catalog games now scan at 0.
- Checkpoint 30 also smooths the chart race playback by preserving interpolated row positions and easing the default smooth-frame cadence.
- Checkpoint 31 added targeted `--audit-missing-cdx-only --needs-history-only` metrics-history recovery, fetched 18 additional archived metrics observations, and cut missing CDX cache files from 355 to 301. A follow-up 50-game audit-only pass found no additional rows and reduced missing CDX cache files to 290.
- Checkpoint 32 recovered 4 additional archived metrics observations, including Deep Sea Hunter 2, Gordo's Oddisey, and Angry Birds Rebuilding Warrior, and cut missing CDX cache files to 275.
- Checkpoint 33 recovered 6 additional archived metrics observations, mainly for Rogue Legend: Tame the Wild plus Button Clicker 2 and Color Number Figure, and cut missing CDX cache files to 259.
- Checkpoint 34 recovered 36 additional archived metrics observations, cut missing CDX cache files to 191, and made the metrics-history fetcher reconcile cached captures safely after interrupted runs.
- Checkpoint 35 recovered 35 additional archived metrics observations and cut missing CDX cache files to 146 using the slower 25-game CDX sweep cadence.
- Checkpoint 36 recovered 15 additional archived metrics observations and cut missing CDX cache files to 104.
- Checkpoint 37 recovered 20 additional archived metrics observations and cut missing CDX cache files to 73.
- Checkpoint 29 removed 238 repeated modern-frame ranked rows and tightened duplicate QA to distinguish valid same-day captures by timestamp; duplicate ranked rows now scan at 0.
- Checkpoint 27 recovered the remaining 2018-01, 2018-02, and 2018-04 gaps with explicitly labeled `homepage_module` fallback rows: 306 January rows, 90 February rows, and 90 April rows.
- Checkpoint 26 recovered May 2009 paginated and top-rated `popular_games` captures, adding 207 ranked rows with observed play counts and rank-offset handling for paginated legacy pages.
- Checkpoint 28 recovered all 10 archived `metrics.json` observations for DPS IDLE and cleared the last known-failures-only metrics case.
- Cached-CDX archived metrics retries recovered 48 additional per-game play-count observations in checkpoint 24.
- 367 mini-catalog games still have no per-game metrics rows, and 2,250 still need deeper page-history backfill.
- Metrics gap audit currently has 0 fresh pending captures, 363 known failed archived captures, 367 unresolved no-CDX cases, 73 missing CDX cache files noted for targeted follow-up, and 0 known-failures-only cases.
- 6 source-conflict play-count decreases are under review after separating 216 stale listing-page echoes into `stale_listing_play_counts.csv`.
- Final chart leaders have current live metrics observations as of 2026-06-30.

## Key Files

- `index.html` - GitHub Pages entry point for the animated observed-plays chart.
- `outputs/kongregate_ranked_games/play_count_bar_chart_race.html` - same chart at the generated output path.
- `outputs/kongregate_ranked_games/play_count_bar_chart_race_data.json` - chart frame data.
- `outputs/kongregate_ranked_games/kongregate_ranked_games.xlsx` - workbook with ranked rows, mini catalog, metrics history, and extraction report.
- `data/processed/ranked_games.csv` - date, game, rank, ranking type, and listing play-count observations.
- `data/processed/mini_catalog.csv` - games that reached top 20 at least once.
- `data/processed/game_play_history.csv` - per-game metrics JSON observations.
- `logs/*report.*` - run reports for extraction and scrape phases.
- `data/processed/data_quality_issues.csv` - current QA issue register.
- `data/processed/catalog_history_priorities.csv` - prioritized metrics-history backfill queue.
- `data/processed/metrics_backfill_gap_audit.csv` - per-game metrics backfill status audit.
- `logs/metrics_backfill_gap_audit_report.*` - summary of fresh pending, known failed, no-CDX, and cache-missing metrics gaps.
- `scripts/` - scraper, extractor, catalog, metrics-history, workbook, and chart builders.

## Rebuild Commands

These commands assume the repository root as the working directory and Python with `lxml` available.

```bash
python3 scripts/extract_ranked_games.py
python3 scripts/build_mini_catalog.py --top-n 20
python3 scripts/fetch_game_metrics_history.py --catalog-offset 0 --catalog-limit 100 --max-fetches 180
python3 scripts/fetch_live_game_metrics.py --statuses no_cdx,known_failures_only,cdx_cache_missing --max-fetches 140
python3 scripts/fetch_game_metrics_history.py --audit-statuses cdx_cache_missing --max-cdx-games 40 --max-fetches 80
python3 scripts/fetch_game_metrics_history.py --audit-missing-cdx-only --needs-history-only --max-cdx-games 50 --max-fetches 50
python3 scripts/fetch_game_metrics_history.py --audit-pending-only --cached-cdx-only --max-fetches 40
python3 scripts/audit_metrics_backfill_gaps.py
node --max-old-space-size=8192 scripts/build_ranked_games_workbook.mjs
node scripts/build_play_count_bar_chart_race.mjs
```

The metrics scrapers are intentionally resumable. Use `--catalog-offset` and `--catalog-limit` to sweep the mini catalog in chunks, `--audit-statuses` or `--audit-pending-only` to target audited archived-metrics gaps, rerun archived metrics with `--retry-failures` for transient Wayback failures, and use `fetch_live_game_metrics.py --input-csv data/processed/final_chart_staleness.csv --statuses '' --refresh` to refresh explicit chart leaders. Live metrics retries skip known failures by default; add `--retry-failures` when intentionally rechecking those pages.

Raw Wayback HTML/JSON caches are not committed here. This repo publishes processed data, reports, scripts, and the static visualization.
