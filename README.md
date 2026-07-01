# Kongregate Plays Data

In-progress public dataset of Kongregate game rankings and observed play counts from archived Kongregate pages and per-game Wayback `metrics.json` captures.

Live chart:

https://dataviking-tech.github.io/kongregate-plays-data/

The live chart fetches `outputs/kongregate_ranked_games/play_count_bar_chart_race_data.json` from this repo at runtime. The Google Sheet is a companion workbook link, not the chart's live data source.

Current Google Sheet workbook:

https://docs.google.com/spreadsheets/d/17uHAfWs6L9ODjWuxCIBv679xu5TpzR5IhodtdymOFYg

## Current Snapshot

- Ranked-list rows: 47,885
- Ranked-list rows with observed play counts: 15,217
- Mini catalog: 2,997 canonical games that reached top 20 in observed rankings
- Per-game play-history rows: 7,932 across 2,667 canonical games
- Observed play-count rows used by the chart: 23,149
- Chart playback: Smooth mode uses 13,105 interpolated month-paced display frames by default; Captures mode exposes all 2,336 observed capture-date frames.
- Ranked-list date range: 2007-01-20 to 2026-07-01
- Per-game play-history date range: 2007-03-24 to 2026-07-01

This scrape is still being expanded. The processed files are coherent snapshots, but coverage is not final.

## Current QA Focus

- Ranked-list freshness is current through the newest recovered Wayback rows as of 2026-07-01, plus current live category pages captured on 2026-07-01. The latest Wayback ranked-list capture remains 2026-06-26, and live chart-leader metrics are refreshed through 2026-07-01.
- 0 cached HTML captures remain empty or corrupted in the ranked-page cache.
- Ranked-page, homepage-fallback, modern-frame, and live-category recovery brought the HTML manifest to 3,351 cached entries with 7,608 known ranked-page failures and 742 known modern-frame failures still recorded.
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
- Checkpoint 48 added an explicit canonical alias map for proven developer/owner renames, merging URL-split identities such as Bowmaster Prelude, CS Portable, Fantastic Contraption, Super Stacker 2, Freefall Tournament, Spiral Knights, Transformice, and Murloc RPG. This reduced the mini catalog from 2,936 to 2,928 canonical games, removed Bowmaster Prelude and CS Portable from the durable no-history gap list, and left Bubble Shooter Exclusive as the only tier-1 no-CDX target.
- Visualization polish after checkpoint 48 reduced Smooth-mode interpolation churn from 19,573 to 6,525 display frames and uses CSS transitions between frames for steadier row motion.
- Checkpoint 49 recovered 19 high-confidence archived game-page observations for Endless Flight 2, increasing game-page history rows to 143 and reducing unresolved no-CDX games from 358 to 357. It also retiered the no-CDX profile so true ranked-list play-count gaps are prioritized ahead of games whose ranked appearances already have listing counts.
- Checkpoint 50 recovered 14 high-confidence archived game-page observations for SpaceWars!, increasing game-page history rows to 157 and reducing unresolved no-CDX games from 357 to 356.
- Post-checkpoint 50 follow-up made `fetch_game_page_history.py` prioritize archived page jobs nearest each game's observed ranked-list dates before older/later captures. Targeted retries for Mecha Galaxy, Boxing Random, Crazy Zombie v2.0 Crossing Hero, Tap Tap Infinity, and Sift Heads World Act 5 found no additional trusted play-count blocks, but the failure ledger now reflects those date-windowed attempts.
- Ranked-list play-count coverage is now tracked monthly in `data/processed/ranked_play_count_coverage_by_month.csv`. It confirms a real listing-layer cliff: 134 ranked months have rows but zero listing play counts, starting in 2014-09 and running through 2025-10. September 2014 rows are present, but the archived HTML uses `new_game_browser_layout-new_layout`, which omits the public play-count text from ranked-list cards.
- `fetch_game_page_history.py` now supports the full `catalog_history_priorities.csv` sweep queue directly, mapping `needs_game_page_history=yes/partial/no` into resumable page-history tiers. A first high-priority catalog probe found no CDX rows for the earliest single-day tier-1 uploads, so broad gap recovery should continue in smaller resumable catalog batches and prioritize games with known longer-lived history.
- Checkpoint 51 added a per-game cap for broad archived page-history sweeps, recovered 12 high-confidence 2008 game-page observations for Sonny and GemCraft, increased archived game-page history rows to 169, and refreshed the chart to 22,153 observed play-count rows.
- Visualization polish after checkpoint 51 keeps long game names clipped inside the label column and drives Smooth mode from elapsed time so busy browsers skip cleanly instead of accumulating small timing pauses.
- Checkpoint 52 recovered 21 additional high-confidence archived game-page observations for GemCraft, extending that 2008 history run through 2008-09-12, increasing archived game-page history rows to 190, and refreshing the chart to 22,174 observed play-count rows.
- Checkpoint 53 added `--profile-offset` and `--profile-limit` to `fetch_game_page_history.py` so the broad page-history queue can advance beyond the first tier games, then recovered 4 high-confidence archived game-page observations for UPGRADE COMPLETE! from July 2009.
- Checkpoint 54 added a separate `--cdx-timeout` to `fetch_game_page_history.py` for faster resumable CDX discovery, then recovered 50 high-confidence archived game-page observations for Boxhead: 2Play Rooms from 2007-06-22 through 2008-09-24. Archived game-page history now has 244 rows, and the chart uses 22,228 observed play-count rows.
- Post-checkpoint 54 recovered 27 additional archived game-page observations for Boxhead: 2Play Rooms, extending that run through 2009-08-23. Archived game-page history now has 271 rows, and the chart uses 22,255 observed play-count rows.
- Visualization polish after checkpoint 54 confirms the live chart fetches the repo JSON at runtime, doubles Smooth-mode interpolation density, and restores short linear transform transitions for steadier row and bar motion.
- Post-checkpoint 55 QA refreshed the gap ledgers, then probed The Company of Myself, Swarm Simulator, The Last Stand 2, plus two unintended sorted-offset targets, UnpuzzleX and Bit Heroes. No additional trusted rows were recovered: Company and Last Stand 2 hit transient CDX connection failures, while the cached Swarm, UnpuzzleX, and Bit Heroes pages either lacked explicit play-count blocks or failed archived fetches. Known archived game-page failures stood at 1,109.
- Checkpoint 56 recovered 61 additional high-confidence/medium-high archived game-page observations for Sonny, spanning 2008-04-20 through 2009-08-25. Archived game-page history now has 332 rows, and the chart uses 22,316 observed play-count rows.
- Post-checkpoint 56 also clarified that `fetch_game_page_history.py --profile-offset` follows the scraper's sorted in-scope queue, not raw CSV row order; use the sorted queue or a name filter when targeting specific games.
- Checkpoint 57 added exact selected-game names to `game_page_history_report` outputs, then recovered 35 additional high-confidence/medium-high archived game-page observations for GemCraft, extending that page-history run through 2009-08-22. Archived game-page history now has 367 rows, and the chart uses 22,351 observed play-count rows.
- Post-checkpoint 57 exact filtered probes checked Learn to Fly 2, Elephant Quest, and Monster Slayers. No additional trusted rows were recovered in those 120-capture batches; the archived pages either lacked explicit play-count blocks or failed archived fetches. Known archived game-page failures now stand at 2,073.
- Visualization polish after checkpoint 57 reduced Smooth-mode frame churn from 39,145 to 9,787 frames, uses subpixel row targets, and lengthens row/bar transforms so playback glides more steadily while still loading the repo JSON at runtime.
- A follow-up cached-CDX page-history pass checked Bloons TD 5, SAS: Zombie Assault 4, and Kingdom Rush. Those 500 archived-capture attempts recovered no additional trusted play-count rows; the refreshed QA scan is unchanged, and known archived game-page failures now stand at 2,573.
- Checkpoint 58 fixed `fetch_live_game_metrics.py --refresh` so valid local caches no longer block explicit live refreshes, then fetched current metrics for all 12 chart leaders. Per-game play history now reaches 2026-07-01, and the chart has 2,336 capture-date frames.
- Checkpoint 59 added `fetch_live_ranked_pages.py` and captured seven reliable current category pages, adding 350 July 1 ranked/category rows with observed listing play counts. Redirecting or ambiguous live routes such as top-rated, most-played, and sorted browse URLs are rejected instead of being mislabeled as rank sources.
- Checkpoint 60 recovered 5 archived `metrics.json` observations for Swarm Simulator: Evolution from 2021-02-09 through 2024-02-23, reducing catalog games without metrics history from 359 to 358. The same pass refreshed the tier-1 no-CDX page-history probe: 170 archived page attempts across 9 high-value gaps found no explicit trusted play-count blocks, and known archived game-page failures now stand at 2,610.
- Checkpoint 61 swept current live `metrics.json` for unresolved no-CDX catalog games, recovered 28 current observations, and confirmed the live no-CDX queue has 0 pending targets. This reduced mini-catalog games without per-game metrics history from 358 to 330, including recoveries for Mecha Galaxy, Boxing Random, Sift Heads World Act 5 - An Exotic Job, Salads by Chef: Merge Сraft, Tracesoccer, Around The Core, and Scooby doo creepy run.
- Checkpoint 62 split play-count QA into clearer buckets: 8 true source-conflict decreases remain under review, 1 suspicious metrics-route decrease is isolated in `suspicious_metric_route_decreases.csv`, and 308 stale/rounded listing-page echoes are separated into `stale_listing_play_counts.csv`.
- Checkpoint 63 retried all 37 known failed archived `metrics.json` captures with extra retries. None recovered; audit coverage stayed at 2,601 games with metrics history and 330 no-CDX/no-history games.
- Checkpoint 64 finished triaging the remaining raw play-count decreases: true monotonic decreases are now 0, 2 suspicious metrics-route anomalies are isolated, and 7 same-day/cross-listing source conflicts are separated into `source_conflict_play_count_decreases.csv`.
- Checkpoint 65 added `fetch_game_page_history.py --cached-html-only` so broad page-history retries can safely reparse only cached archived HTML without opening new Wayback page fetches. A cached-only catalog-priority sweep considered 2,247 tier-1/tier-2 games, 10,938 cached-CDX page jobs, and 955 cached HTML failures; it recovered 0 additional trusted play-count rows, confirming those cached misses mostly lack static count text and should be pursued through metrics endpoints or new targeted capture strategies.
- Checkpoint 66 added opt-in `fetch_game_metrics_history.py --expanded-route-variants` for probing explicit `http`/`https` and `/en/games` archived metrics routes without slowing normal sweeps. A three-game no-CDX probe found 0 new archived metrics CDX rows, so the highest-priority no-CDX cases still appear genuinely unarchived on the metrics endpoint.
- Checkpoint 67 expanded default live ranked-page coverage with `multiplayer`, `mmo`, `adventure-rpg`, `sports-racing`, `strategy-defense`, `more`, and `card` category pages. The July 1 live sweep added 349 ranked rows with observed listing play counts, grew the mini catalog to 2,997 games, and a follow-up live-metrics pass recovered current observations for all 66 newly exposed catalog games.
- Visualization polish after checkpoint 67 removes the Smooth-mode rank-snap jitter by sorting interpolated frames on continuous rank position, preserving sub-slot row motion, and lengthening row/bar transforms. The chart still fetches `outputs/kongregate_ranked_games/play_count_bar_chart_race_data.json` from the repo at runtime.
- Checkpoint 29 removed 238 repeated modern-frame ranked rows and tightened duplicate QA to distinguish valid same-day captures by timestamp; duplicate ranked rows now scan at 0.
- Checkpoint 27 recovered the remaining 2018-01, 2018-02, and 2018-04 gaps with explicitly labeled `homepage_module` fallback rows: 306 January rows, 90 February rows, and 90 April rows.
- Checkpoint 26 recovered May 2009 paginated and top-rated `popular_games` captures, adding 207 ranked rows with observed play counts and rank-offset handling for paginated legacy pages.
- Checkpoint 28 recovered all 10 archived `metrics.json` observations for DPS IDLE and cleared the last known-failures-only metrics case.
- Cached-CDX archived metrics retries recovered 48 additional per-game play-count observations in checkpoint 24.
- 330 mini-catalog games still have no per-game play-history rows, and 2,247 still need deeper page-history backfill.
- Metrics gap audit currently has 0 fresh pending captures, 37 known failed archived captures, 330 games without any per-game metrics rows, and 157 missing CDX cache files.
- The no-CDX profile splits the 330 no-history/no-CDX games still needing triage into 7 high-value follow-up games: 6 tier-1 repeated ranked-list count gaps, 1 complete-listing multi-capture target, 86 single-capture complete-listing candidates, and 237 low-information single-capture rows with no listing play count.
- True monotonic play-count decreases now scan at 0. Two suspicious metrics-route decreases are isolated in `suspicious_metric_route_decreases.csv`, 7 same-day/cross-listing source conflicts are isolated in `source_conflict_play_count_decreases.csv`, and 353 stale or rounded listing-page echoes are separated into `stale_listing_play_counts.csv`. The chart uses max-observed play counts so these raw-source conflicts do not create visual count drops.
- Final chart leaders have current live metrics observations as of 2026-07-01.

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
- `data/processed/suspicious_metric_route_decreases.csv` - metrics-route drops that look like alias/route anomalies rather than true counter decreases.
- `data/processed/source_conflict_play_count_decreases.csv` - same-day or cross-listing count conflicts retained as raw observations but excluded from true decrease counts.
- `data/processed/ranked_play_count_coverage_by_month.csv` - monthly ranked-list play-count coverage and layout hints for missing-count months.
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
python3 scripts/fetch_game_metrics_history.py --audit-statuses no_cdx --max-cdx-games 3 --cdx-only --expanded-route-variants
python3 scripts/fetch_game_page_history.py --tiers 1 --max-cdx-games 9 --variant-limit 2 --max-fetches 160
python3 scripts/fetch_game_page_history.py --tiers 1 --game-name-contains 'diaper,papa,swords' --cached-cdx-only --max-fetches 120
python3 scripts/fetch_game_page_history.py --tiers 1 --game-name-contains ufomania --cached-cdx-only --variant-limit 2 --max-fetches 60
python3 scripts/fetch_game_page_history.py --input-csv data/processed/catalog_history_priorities.csv --tiers 1,2 --cached-cdx-only --cached-html-only --retry-failures --sleep 0 --cdx-sleep 0
python3 scripts/fetch_live_ranked_pages.py
python3 scripts/audit_metrics_backfill_gaps.py
python3 scripts/profile_metrics_no_cdx_gaps.py
python3 scripts/scan_data_quality.py --as-of 2026-07-01
node --max-old-space-size=8192 scripts/build_ranked_games_workbook.mjs
node scripts/build_play_count_bar_chart_race.mjs
```

The metrics and page-history scrapers are intentionally resumable. Use `--catalog-offset` and `--catalog-limit` to sweep the mini catalog in chunks, `--audit-statuses` or `--audit-pending-only` to target audited archived-metrics gaps, rerun archived metrics with `--retry-failures` for transient Wayback failures, and use `fetch_live_game_metrics.py --input-csv data/processed/final_chart_staleness.csv --statuses '' --refresh` to refresh explicit chart leaders. `fetch_game_page_history.py` is conservative: it stores parsed rows only when an archived game page exposes an explicit main play-count block. For the full page-history sweep, point it at `data/processed/catalog_history_priorities.csv` and run small tiered batches, for example `python3 scripts/fetch_game_page_history.py --input-csv data/processed/catalog_history_priorities.csv --tiers=2 --profile-offset 24 --profile-limit 3 --max-cdx-games 3 --variant-limit 2 --max-fetches 80 --max-jobs-per-game 80 --cached-cdx-only --cdx-timeout 5`. Use `--cached-html-only` with `--retry-failures` to safely test parser improvements against already-downloaded HTML without fetching new archived pages. Use `--profile-offset`, `--profile-limit`, `--game-name-contains`, `--cached-cdx-only`, `--max-jobs-per-game`, and `--cdx-timeout` for focused resumable page-history recovery. Live metrics retries skip known failures by default; add `--retry-failures` when intentionally rechecking those pages.

Raw Wayback HTML/JSON caches are not committed here. This repo publishes processed data, reports, scripts, and the static visualization.
