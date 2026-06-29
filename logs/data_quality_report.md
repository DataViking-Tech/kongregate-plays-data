# Kongregate Data Quality Report

- Run timestamp: 2026-06-29T08:16:06Z
- As of: 2026-06-29
- Ranked rows: 8140
- Ranked rows with play counts: 4685
- Ranked date range: 2007-01-20 to 2026-06-26
- Mini catalog games: 743
- Metrics history rows/games: 2348 / 184
- Metrics date range: 2013-09-18 to 2026-05-19
- Invalid cached HTML files: 105

## Top Issues

- HIGH cache/invalid_cached_html_files: 105 - Retry affected captures; these files are empty or corrupted and cannot be parsed.
- MEDIUM coverage/months_without_ranked_captures: 134 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH metrics/catalog_games_without_metrics_history: 457 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 381 - Continue per-game metrics history backfill.
- HIGH chart/final_top_chart_entries_stale_over_one_year: 9 - Prioritize metrics histories for stale high-play games still dominating final chart ranks.
- LOW dedupe/duplicate_ranked_rows: 576 - Review duplicate key handling by date/source/rank/game.
- MEDIUM identity/games_with_multiple_url_variants: 148 - Use canonical URL keys for joins and charting; consider canonicalizing processed rows.

## Top Metrics Backfill Priorities

- Robo-Jump (score 3351, best rank 1, metrics rows 0)
- Aground (score 3253, best rank 2, metrics rows 0)
- Decision (score 3253, best rank 2, metrics rows 0)
- Madnes Project Nexus Party mod III (score 3253, best rank 2, metrics rows 0)
- Wonderputt (score 3253, best rank 2, metrics rows 0)
- Achievement Unlocked 2 (score 3251, best rank 2, metrics rows 0)
- Caralhinhos Voadores - Age Of Delicia (score 3251, best rank 2, metrics rows 0)
- Pre-Civilization Bronze Age (score 3251, best rank 2, metrics rows 0)
- Accelerator (score 3153, best rank 3, metrics rows 0)
- Drakenlords: CCG Cards Duels (score 3153, best rank 3, metrics rows 0)
- There is no game (score 3153, best rank 3, metrics rows 0)
- Trimps (score 3153, best rank 3, metrics rows 0)
