# Kongregate Plays Data

In-progress public dataset of Kongregate game rankings and observed play counts from archived Kongregate pages and per-game Wayback `metrics.json` captures.

Live chart:

https://dataviking-tech.github.io/kongregate-plays-data/

The live chart fetches `outputs/kongregate_ranked_games/play_count_bar_chart_race_data.json` from this repo at runtime. The Google Sheet is a companion workbook link, not the chart's live data source.

Current Google Sheet workbook:

https://docs.google.com/spreadsheets/d/19mWDxN3t0bcRTbUNUgdOOwY-XcRzvpGd5r1BBzqN-i0

## Current Snapshot

- Ranked-list rows: 47,186
- Ranked-list rows with observed play counts: 14,518
- Mini catalog: 2,936 canonical games that reached top 20 in observed rankings
- Per-game play-history rows: 7,590 across 2,575 canonical games
- Observed play-count rows used by the chart: 22,108
- Chart playback: Smooth mode uses 19,573 interpolated month-paced display frames by default; Captures mode exposes all 2,251 observed capture-date frames.
- Ranked-list date range: 2007-01-20 to 2026-06-26
- Per-game play-history date range: 2007-03-24 to 2026-06-30

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
- Visualization polish after checkpoint 37 doubled Smooth-mode interpolation density, kept animated rows in compact rank lanes, and confirmed the live chart fetches the repo JSON at runtime.
- Checkpoint 38 recovered 6 additional archived metrics observations and cut missing CDX cache files to 71.
- Checkpoint 39 recovered 2 additional archived metrics observations from the high-priority catalog retry sweep.
- Checkpoint 40 recovered 23 additional archived metrics observations from broader high-priority catalog chunks and reduced known failed archived captures to 348.
- Checkpoint 41 recovered 71 additional archived metrics observations from catalog chunks 480, 600, 720, 960, 1080, and 1200; it also smoothed chart-race row motion and reduced known failed archived captures to 277.
- Checkpoint 42 recovered 51 additional archived metrics observations from catalog chunks 1320, 1440, and 1560, then confirmed chunk 1680 was effectively dry; known failed archived captures fell to 226.
- Checkpoint 43 completed the remaining chunked mini-catalog sweep from offsets 1800 through 2880, recovered 94 additional archived metrics observations, and reduced known failed archived captures to 132.
- Checkpoint 44 added `--audit-known-failures-only`, recovered 102 additional archived metrics observations from targeted missing-CDX and known-failure retry passes, reduced missing CDX cache files to 17, and reduced known failed archived captures to 47.
- Checkpoint 45 recovered 20 additional archived metrics observations from final missing-CDX and known-failure retry passes, reduced missing CDX cache files to 0, and reduced known failed archived captures to 37.
- Checkpoint 46 added conservative archived game-page play-count recovery via `fetch_game_page_history.py`, recovered 57 high-confidence page-history observations for Super Stacker 2 and Fantastic Contraption, and reduced unresolved no-CDX games from 367 to 365.
- Checkpoint 47 recovered 67 additional archived game-page observations for Diaper Dash, Papa Louie, swords and sandals 2, and UFOMania; game-page history now has 124 rows and unresolved no-CDX games fell to 361. Smooth chart playback now uses direct per-frame transforms in Smooth mode to reduce visual jitter while keeping eased capture-step playback.
- Checkpoint 29 removed 238 repeated modern-frame ranked rows and tightened duplicate QA to distinguish valid same-day captures by timestamp; duplicate ranked rows now scan at 0.
- Checkpoint 27 recovered the remaining 2018-01, 2018-02, and 2018-04 gaps with explicitly labeled `homepage_module` fallback rows: 306 January rows, 90 February rows, and 90 April rows.
- Checkpoint 26 recovered May 2009 paginated and top-rated `popular_games` captures, adding 207 ranked rows with observed play counts and rank-offset handling for paginated legacy pages.
- Checkpoint 28 recovered all 10 archived `metrics.json` observations for DPS IDLE and cleared the last known-failures-only metrics case.
- Cached-CDX archived metrics retries recovered 48 additional per-game play-count observations in checkpoint 24.
- 361 mini-catalog games still have no per-game play-history rows, and 2,250 still need deeper page-history backfill.
- Metrics gap audit currently has 0 fresh pending captures, 37 known failed archived captures, 361 unresolved no-CDX cases, and 0 missing CDX cache files.
- The no-CDX profile splits those 361 games into 110 follow-up targets with observed listing counts, 11 repeated ranking-only targets, and 240 low-information single-capture rows with no listing play count.
- 6 source-conflict play-count decreases are under review after separating 227 stale listing-page echoes into `stale_listing_play_counts.csv`.
- Final chart leaders have current live metrics observations as of 2026-06-30.

## Key Files

- `index.html` - GitHub Pages entry point for the animated observed-plays chart.
- `outputs/kongregate_ranked_games/play_count_bar_chart_race.html` - same chart at the generated output path.
- `outputs/kongregate_ranked_games/play_count_bar_chart_race_data.json` - chart frame data.
- `outputs/kongregate_ranked_games/kongregate_ranked_games.xlsx` - workbook with ranked rows, mini catalog, metrics history, and extraction report.
- `data/processed/ranked_games.csv` - date, game, rank, ranking type, and listing play-count observations.
- `data/processed/mini_catalog.csv` - games that reached top 20 at least once.
- `data/processed/game_play_history.csv` - per-game metrics JSON, live metrics, and archived game-page observations.
- `logs/*report.*` - run reports for extraction and scrape phases.
- `data/processed/data_quality_issues.csv` - current QA issue register.
- `data/processed/catalog_history_priorities.csv` - prioritized metrics-history backfill queue.
- `data/processed/metrics_backfill_gap_audit.csv` - per-game metrics backfill status audit.
- `logs/metrics_backfill_gap_audit_report.*` - summary of fresh pending, known failed, no-CDX, and cache-missing metrics gaps.
- `data/processed/metrics_no_cdx_profile.csv` and `logs/metrics_no_cdx_profile_report.*` - triage profile for the remaining no-CDX games.
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
python3 scripts/fetch_game_metrics_history.py --audit-known-failures-only --cached-cdx-only --max-fetches 80 --retry-failures
python3 scripts/fetch_game_metrics_history.py --audit-pending-only --cached-cdx-only --max-fetches 40
python3 scripts/fetch_game_page_history.py --tiers 1 --max-cdx-games 9 --variant-limit 2 --max-fetches 160
python3 scripts/fetch_game_page_history.py --tiers 1 --game-name-contains 'diaper,papa,swords' --cached-cdx-only --max-fetches 120
python3 scripts/fetch_game_page_history.py --tiers 1 --game-name-contains ufomania --cached-cdx-only --variant-limit 2 --max-fetches 60
python3 scripts/audit_metrics_backfill_gaps.py
python3 scripts/profile_metrics_no_cdx_gaps.py
node --max-old-space-size=8192 scripts/build_ranked_games_workbook.mjs
node scripts/build_play_count_bar_chart_race.mjs
```

The metrics and page-history scrapers are intentionally resumable. Use `--catalog-offset` and `--catalog-limit` to sweep the mini catalog in chunks, `--audit-statuses` or `--audit-pending-only` to target audited archived-metrics gaps, rerun archived metrics with `--retry-failures` for transient Wayback failures, and use `fetch_live_game_metrics.py --input-csv data/processed/final_chart_staleness.csv --statuses '' --refresh` to refresh explicit chart leaders. `fetch_game_page_history.py` is conservative: it stores parsed rows only when an archived game page exposes an explicit main play-count block; use `--game-name-contains` and `--cached-cdx-only` for focused resumable page-history recovery. Live metrics retries skip known failures by default; add `--retry-failures` when intentionally rechecking those pages.

Raw Wayback HTML/JSON caches are not committed here. This repo publishes processed data, reports, scripts, and the static visualization.
