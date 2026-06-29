# Kongregate Plays Data

In-progress public dataset of Kongregate game rankings and observed play counts from archived Kongregate pages and per-game Wayback `metrics.json` captures.

Live chart, once GitHub Pages is enabled in repository settings:

https://dataviking-tech.github.io/kongregate-plays-data/

## Current Snapshot

- Ranked-list rows: 8,140
- Ranked-list rows with observed play counts: 4,685
- Mini catalog: 743 games that reached top 20 in observed rankings
- Per-game metrics history rows: 2,120 across 167 canonical games
- Observed play-count rows used by the chart: 6,805
- Ranked-list date range: 2007-01-20 to 2026-06-26
- Metrics-history date range: 2013-09-18 to 2026-05-19

This scrape is still being expanded. The processed files are coherent snapshots, but coverage is not final.

## Current QA Focus

- Ranked-list freshness is current through the newest recovered Wayback rows as of 2026-06-29.
- 105 cached HTML captures remain empty or corrupted and are queued for retry/backfill.
- 134 historical months still have no ranked-list captures in the processed dataset.
- 485 mini-catalog games still need per-game metrics history backfill.

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
- `scripts/` - scraper, extractor, catalog, metrics-history, workbook, and chart builders.

## Rebuild Commands

These commands assume the repository root as the working directory and Python with `lxml` available.

```bash
python3 scripts/extract_ranked_games.py
python3 scripts/build_mini_catalog.py --top-n 20
python3 scripts/fetch_game_metrics_history.py --catalog-offset 0 --catalog-limit 100 --max-fetches 180
node scripts/build_play_count_bar_chart_race.mjs
```

The metrics scraper is intentionally resumable. Use `--catalog-offset` and `--catalog-limit` to sweep the mini catalog in chunks, and rerun with `--retry-failures` for a later pass over transient Wayback failures.

Raw Wayback HTML/JSON caches are not committed here. This repo publishes processed data, reports, scripts, and the static visualization.
