# Archived Count Source Probe

- Generated: 2026-07-03T22:04:11Z
- Target games: 9
- Status filter: transient_failures_remaining
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 9
- Endpoint candidates checked: 17
- Candidate observation rows: 17
- CDX status counts: fetched=17
- CDX rows found: 4
- Candidates with CDX rows: 4
- Payloads with count-like signals: 4
- Parsed play-count rows: 4
- Deduped recovered play-count observations: 678 (2 new this run)
- Accumulated probe-history rows: 16324 (17 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Dragon Fortress | metrics_json | `http://www.kongregate.com/games/littlegiantworld/dragon-fortress/metrics.json` | `http://www.kongregate.com/games/littlegiantworld/dragon-fortress/metrics.json` | gameplays_count_with_delimiter | 277764 |
| Dragon Fortress | metrics_json | `https://www.kongregate.com/games/littlegiantworld/dragon-fortress/metrics.json` | `http://www.kongregate.com/games/littlegiantworld/dragon-fortress/metrics.json` | gameplays_count_with_delimiter | 277764 |
| GameToilet Mobile#2 : Watch Paint Dry | metrics_json | `http://www.kongregate.com/games/kingbaggot/gametoilet-mobile-2-watch-paint-dry/metrics.json` | `https://www.kongregate.com/games/kingbaggot/gametoilet-mobile-2-watch-paint-dry/metrics.json` | gameplays_count_with_delimiter | 901 |
| GameToilet Mobile#2 : Watch Paint Dry | metrics_json | `https://www.kongregate.com/games/kingbaggot/gametoilet-mobile-2-watch-paint-dry/metrics.json` | `https://www.kongregate.com/games/kingbaggot/gametoilet-mobile-2-watch-paint-dry/metrics.json` | gameplays_count_with_delimiter | 901 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Dragon Fortress | metrics_json | `http://www.kongregate.com/games/littlegiantworld/dragon-fortress/metrics.json` | `http://www.kongregate.com/games/littlegiantworld/dragon-fortress/metrics.json` | 1 |
| Dragon Fortress | metrics_json | `https://www.kongregate.com/games/littlegiantworld/dragon-fortress/metrics.json` | `http://www.kongregate.com/games/littlegiantworld/dragon-fortress/metrics.json` | 1 |
| GameToilet Mobile#2 : Watch Paint Dry | metrics_json | `http://www.kongregate.com/games/kingbaggot/gametoilet-mobile-2-watch-paint-dry/metrics.json` | `https://www.kongregate.com/games/kingbaggot/gametoilet-mobile-2-watch-paint-dry/metrics.json` | 1 |
| GameToilet Mobile#2 : Watch Paint Dry | metrics_json | `https://www.kongregate.com/games/kingbaggot/gametoilet-mobile-2-watch-paint-dry/metrics.json` | `https://www.kongregate.com/games/kingbaggot/gametoilet-mobile-2-watch-paint-dry/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`