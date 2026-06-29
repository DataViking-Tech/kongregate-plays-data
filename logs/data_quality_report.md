# Kongregate Data Quality Report

- Run timestamp: 2026-06-29T11:46:33Z
- As of: 2026-06-29
- Ranked rows: 8625
- Ranked rows with play counts: 4845
- Ranked date range: 2007-01-20 to 2026-06-26
- Mini catalog games: 749
- Metrics history rows/games: 3736 / 552
- Metrics date range: 2013-09-18 to 2026-06-29
- Invalid cached HTML files: 85

## Top Issues

- HIGH cache/invalid_cached_html_files: 85 - Retry affected captures; these files are empty or corrupted and cannot be parsed.
- MEDIUM coverage/months_without_ranked_captures: 132 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH metrics/catalog_games_without_metrics_history: 49 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 386 - Continue per-game metrics history backfill.
- LOW dedupe/duplicate_ranked_rows: 739 - Review duplicate key handling by date/source/rank/game.
- MEDIUM identity/games_with_multiple_url_variants: 150 - Use canonical URL keys for joins and charting; consider canonicalizing processed rows.

## Top Metrics Backfill Priorities

- Caralhinhos Voadores - Age Of Delicia (score 3251, best rank 2, metrics rows 0)
- A Kongergate Special (score 3151, best rank 3, metrics rows 0)
- Mutilate-a-Doll 2 (score 2987, best rank 1, metrics rows 102)
- Swords and Souls (score 2946, best rank 1, metrics rows 51)
- Bowmaster Prelude (score 2912, best rank 1, metrics rows 0)
- Bowmaster Prelude (score 2905, best rank 1, metrics rows 0)
- BLOB KILLS BALL! (score 2901, best rank 1, metrics rows 0)
- Maddening Foolishness (score 2901, best rank 1, metrics rows 0)
- Stafforb's Worst Pokemon Battle (score 2901, best rank 1, metrics rows 0)
- Bit Heroes (score 2896, best rank 1, metrics rows 83)
- NGU IDLE (score 2896, best rank 1, metrics rows 107)
- Clicker Heroes (score 2894, best rank 1, metrics rows 27)
