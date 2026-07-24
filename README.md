# Kongregate Plays Data

A public, evidence-backed record of Kongregate rankings and observed game play counts, assembled from archived Kongregate pages, archived per-game `metrics.json` captures, and current category pages.

[Explore the animated ranking chart](https://dataviking-tech.github.io/kongregate-plays-data/) | [Open the companion Google Sheet](https://docs.google.com/spreadsheets/d/1qOYvswGlueASBmVQ3__IR1mMSXevYxonSEfYmcZF5qw)

## Status

This is the completed Kongregate/Wayback v1 dataset. The final audit classifies every remaining recovery priority, verifies that all ranked months have aggregate as-of play-count coverage, and finds no true play-count decreases in the published series.

- 49,982 ranked-list rows from 2007-01-20 through 2026-07-04
- 2,998 canonical games that reached the top 20 in an observed ranking
- 44,906 ranked rows (89.84%) with an observed play count on or before the ranking date
- 9,124 per-game history observations across 2,687 games
- 26,438 observed play-count records used by the chart

The animated chart reads its data directly from this repository at runtime: `outputs/kongregate_ranked_games/play_count_bar_chart_race_data.json`. The Google Sheet is a companion workbook, not the chart's data source.

## Coverage And Caveats

The remaining 5,076 ranked rows without an aggregate as-of count are documented rather than silently filled. The final audit places each affected game in an evidence bucket: an exact metrics archive begins after the missing period, no usable archived metrics capture exists for the period, archived pages expose dynamic placeholders without a count, or no usable archived page capture exists.

This is therefore complete for the available Kongregate and Wayback evidence. Filling those final gaps would require a materially different source, such as third-party records, developer archives, or private platform data.

Useful starting points:

- [V1 completion audit](logs/v1_completion_audit_report.md)
- [Data-quality report](logs/data_quality_report.md)
- [No-history evidence summary](logs/no_history_evidence_summary_report.md)
- [Full recovery-priority table](data/processed/v1_completion_audit.csv)

## Repository Guide

```text
data/processed/   Published tables, CSVs, JSON exports, and coverage audits
outputs/          Workbook and static chart artifacts served by GitHub Pages
scripts/          Extractors, recovery probes, builders, and QA checks
logs/             Generated machine-readable and narrative run reports
logs/progress/    Historical checkpoint index and release notes
index.html        GitHub Pages entry point
```

The most useful data files are:

- `data/processed/ranked_games.csv`: ranking date, game, rank, source, and direct listing-count observations.
- `data/processed/ranked_games_observed_plays.csv.gz`: ranked rows enriched with the highest observed count on or before each ranking date.
- `data/processed/game_play_history.csv`: per-game metrics, live metrics, and archived game-page observations.
- `data/processed/mini_catalog.csv`: the canonical top-20 mini catalog and recovered game IDs.
- `data/processed/game_lifecycle_catalog.csv`: first/last observed dates, source evidence, and cautious removal evidence.
- `data/processed/game_taxonomy.csv`: versioned genre, engagement, social-platform review, developer-group, and series-group labels with confidence and evidence fields.
- `outputs/kongregate_ranked_games/kongregate_ranked_games.xlsx`: workbook containing the published tables and reports.

## Reports

`logs/` intentionally keeps generated reports at a stable, flat path so the data pipeline can rewrite them without special handling. [The logs guide](logs/README.md) groups them by purpose for humans, and [the progress index](logs/progress/README.md) keeps the long checkpoint trail out of this README.

## Rebuilding

The scripts are resumable, and raw Wayback caches are intentionally not committed. A normal refresh uses the existing processed snapshot as its starting point:

```bash
python3 scripts/extract_ranked_games.py
python3 scripts/build_mini_catalog.py --top-n 20
python3 scripts/build_ranked_games_observed_plays.py
python3 scripts/scan_data_quality.py --as-of 2026-07-05
python3 scripts/build_game_lifecycle_catalog.py
python3 scripts/build_game_taxonomy.py
python3 scripts/summarize_no_history_evidence.py
python3 scripts/build_v1_completion_audit.py --processed-through-priority-rank 189
node --max-old-space-size=8192 scripts/build_ranked_games_workbook.mjs
node scripts/build_play_count_bar_chart_race.mjs
```

The recovery tools in `scripts/` can continue targeted Wayback work, but the v1 audit should be refreshed after any data change before treating a new snapshot as published.

## License

The scripts and other software are available under the [MIT License](LICENSE). Original compiled data, reports, visualizations, and documentation are available under [CC BY 4.0](LICENSE-DATA.md). See [NOTICE.md](NOTICE.md) for source and attribution guidance; no rights are granted to the underlying games, trademarks, or third-party archive material.
