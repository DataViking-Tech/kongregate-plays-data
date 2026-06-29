# Kongregate Data Quality Report

- Run timestamp: 2026-06-29T12:29:25Z
- As of: 2026-06-29
- Ranked rows: 10053
- Ranked rows with play counts: 5414
- Ranked date range: 2007-01-20 to 2026-06-26
- Mini catalog games: 924
- Metrics history rows/games: 4006 / 589
- Metrics date range: 2013-09-18 to 2026-06-29
- Invalid cached HTML files: 9

## Top Issues

- HIGH cache/invalid_cached_html_files: 9 - Retry affected captures; these files are empty or corrupted and cannot be parsed.
- MEDIUM coverage/months_without_ranked_captures: 116 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH metrics/catalog_games_without_metrics_history: 85 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 542 - Continue per-game metrics history backfill.
- LOW dedupe/duplicate_ranked_rows: 819 - Review duplicate key handling by date/source/rank/game.
- MEDIUM identity/games_with_multiple_url_variants: 224 - Use canonical URL keys for joins and charting; consider canonicalizing processed rows.

## Top Metrics Backfill Priorities

- Caralhinhos Voadores - Age Of Delicia (score 3251, best rank 2, metrics rows 0)
- A Kongergate Special (score 3151, best rank 3, metrics rows 0)
- Mutilate-a-Doll 2 (score 2990, best rank 1, metrics rows 102)
- Swords and Souls (score 2950, best rank 1, metrics rows 51)
- NGU IDLE (score 2931, best rank 1, metrics rows 107)
- Bit Heroes (score 2929, best rank 1, metrics rows 83)
- Bloons TD 5 (score 2928, best rank 1, metrics rows 60)
- Swords and Souls (score 2923, best rank 1, metrics rows 51)
- UnpuzzleX (score 2915, best rank 1, metrics rows 31)
- Bowmaster Prelude (score 2912, best rank 1, metrics rows 0)
- Bowmaster Prelude (score 2905, best rank 1, metrics rows 0)
- BLOB KILLS BALL! (score 2901, best rank 1, metrics rows 0)
