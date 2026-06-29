# Kongregate Data Quality Report

- Run timestamp: 2026-06-29T14:52:08Z
- As of: 2026-06-29
- Ranked rows: 14133
- Ranked rows with play counts: 7154
- Ranked date range: 2007-01-20 to 2026-06-26
- Mini catalog games: 1319
- Metrics history rows/games: 4138 / 620
- Metrics date range: 2013-09-18 to 2026-06-29
- Invalid cached HTML files: 0

## Top Issues

- MEDIUM coverage/months_without_ranked_captures: 100 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH metrics/catalog_games_without_metrics_history: 396 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 881 - Continue per-game metrics history backfill.
- LOW dedupe/duplicate_ranked_rows: 1506 - Review duplicate key handling by date/source/rank/game.
- MEDIUM identity/games_with_multiple_url_variants: 280 - Use canonical URL keys for joins and charting; consider canonicalizing processed rows.

## Top Metrics Backfill Priorities

- [Future Mode] The Warriors Way 0.2 (score 3351, best rank 1, metrics rows 0)
- Digimon Pyramid Adventure (score 3351, best rank 1, metrics rows 0)
- Energy Bay (score 3351, best rank 1, metrics rows 0)
- Filler Snake (score 3351, best rank 1, metrics rows 0)
- Halloween Spooky Motocross (score 3351, best rank 1, metrics rows 0)
- Journey through Wind and Fire I (score 3351, best rank 1, metrics rows 0)
- Roller Ball Plat (score 3351, best rank 1, metrics rows 0)
- Run Bird Run Online (score 3351, best rank 1, metrics rows 0)
- Shootrio (score 3351, best rank 1, metrics rows 0)
- Simple factory idle game (score 3351, best rank 1, metrics rows 0)
- Soul Shadows (score 3351, best rank 1, metrics rows 0)
- SuperBall Idle (score 3351, best rank 1, metrics rows 0)
