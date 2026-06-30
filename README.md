# Kongregate Plays Data

In-progress public dataset of Kongregate game rankings and observed play counts from archived Kongregate pages and per-game Wayback `metrics.json` captures.

Live chart:

https://dataviking-tech.github.io/kongregate-plays-data/

The live chart fetches `outputs/kongregate_ranked_games/play_count_bar_chart_race_data.json` from this repo at runtime. The Google Sheet is a companion workbook link, not the chart's live data source.

Current Google Sheet workbook:

https://docs.google.com/spreadsheets/d/1M52sKSlnfr0MLD_8_RIF-5Y9qPZsC-jc8El5DcVnEVA

## Current Snapshot

- Ranked-list rows: 36,325
- Ranked-list rows with observed play counts: 11,087
- Mini catalog: 3,007 games that reached top 20 in observed rankings
- Per-game metrics history rows: 5,142 across 1,293 canonical games
- Observed play-count rows used by the chart: 16,229
- Chart playback: Smooth mode uses 2,331 interpolated display frames by default; Captures mode exposes all 1,819 observed capture-date frames.
- Ranked-list date range: 2007-01-20 to 2026-06-26
- Metrics-history date range: 2013-09-18 to 2026-06-29

This scrape is still being expanded. The processed files are coherent snapshots, but coverage is not final.

## Current QA Focus

- Ranked-list freshness is current through the newest recovered Wayback rows as of 2026-06-30.
- 0 cached HTML captures remain empty or corrupted in the ranked-page cache.
- Ranked scrape backlog now has 1,015 pending captures, alongside 2,356 valid cached captures and 7,150 known failed captures.
- 66 historical months still have no ranked-list captures in the processed dataset.
- 1,301 mini-catalog games still have no per-game metrics rows, and 2,311 still need deeper page-history backfill.
- Metrics gap audit currently has 0 fresh pending captures and 675 missing CDX cache files; remaining unresolved games include 660 no-CDX cases, 592 CDX-cache-missing cases, and 49 games with known failures only.
- 0 true play-count decreases remain after separating 123 stale listing-page echoes into `stale_listing_play_counts.csv`.
- Final chart leaders have current live metrics observations as of 2026-06-29.

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
python3 scripts/fetch_live_game_metrics.py --max-fetches 140
python3 scripts/audit_metrics_backfill_gaps.py
node --max-old-space-size=8192 scripts/build_ranked_games_workbook.mjs
node scripts/build_play_count_bar_chart_race.mjs
```

The metrics scrapers are intentionally resumable. Use `--catalog-offset` and `--catalog-limit` to sweep the mini catalog in chunks, rerun archived metrics with `--retry-failures` for transient Wayback failures, and use `fetch_live_game_metrics.py --input-csv data/processed/final_chart_staleness.csv --statuses '' --refresh` to refresh explicit chart leaders.

Raw Wayback HTML/JSON caches are not committed here. This repo publishes processed data, reports, scripts, and the static visualization.
