# Kongregate Data Quality Report

- Run timestamp: 2026-06-29T04:46:25Z
- As of: 2026-06-29
- Ranked rows: 8140
- Ranked rows with play counts: 4685
- Ranked date range: 2007-01-20 to 2026-06-26
- Mini catalog games: 743
- Metrics history rows/games: 355 / 21
- Metrics date range: 2014-08-07 to 2025-10-01
- Invalid cached HTML files: 105

## Top Issues

- HIGH cache/invalid_cached_html_files: 105 - Retry affected captures; these files are empty or corrupted and cannot be parsed.
- MEDIUM coverage/months_without_ranked_captures: 134 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH metrics/catalog_games_without_metrics_history: 711 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 381 - Continue per-game metrics history backfill.
- HIGH chart/final_top_chart_entries_stale_over_one_year: 9 - Prioritize metrics histories for stale high-play games still dominating final chart ranks.
- LOW dedupe/duplicate_ranked_rows: 576 - Review duplicate key handling by date/source/rank/game.
- MEDIUM identity/games_with_multiple_url_variants: 148 - Use canonical URL keys for joins and charting; consider canonicalizing processed rows.

## Top Metrics Backfill Priorities

- Crusaders of the Lost Idols (score 3391, best rank 1, metrics rows 0)
- Realm Grinder (score 3385, best rank 1, metrics rows 0)
- NGU IDLE (score 3379, best rank 1, metrics rows 0)
- Bit Heroes (score 3377, best rank 1, metrics rows 0)
- AdVenture Capitalist (score 3374, best rank 1, metrics rows 0)
- Incremancer (score 3368, best rank 1, metrics rows 0)
- Swarm Simulator (score 3368, best rank 1, metrics rows 0)
- Retro Bowl (score 3366, best rank 1, metrics rows 0)
- The King's League: Odyssey (score 3365, best rank 1, metrics rows 0)
- Crush The Castle 2 (score 3353, best rank 1, metrics rows 0)
- Frantic Frigates (score 3353, best rank 1, metrics rows 0)
- Plinko Idle (score 3353, best rank 1, metrics rows 0)
