# Archived Count Source Probe

- Generated: 2026-07-03T18:58:15Z
- Target games: 8
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 8
- Endpoint candidates checked: 16
- Candidate observation rows: 20
- CDX status counts: cached=4, fetched=16
- CDX rows found: 18
- Candidates with CDX rows: 6
- Payloads with count-like signals: 6
- Parsed play-count rows: 6
- Deduped recovered play-count observations: 594 (2 new this run)
- Accumulated probe-history rows: 15017 (20 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Necromancer's Quest Beta | metrics_json | `http://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | gameplays_count_with_delimiter | 11149 |
| Necromancer's Quest Beta | metrics_json | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | gameplays_count_with_delimiter | 11149 |
| Necromancer's Quest Beta | metrics_json | `http://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | gameplays_count_with_delimiter | 11139 |
| Necromancer's Quest Beta | metrics_json | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | gameplays_count_with_delimiter | 11139 |
| Necromancer's Quest Beta | metrics_json | `http://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | gameplays_count_with_delimiter | 11137 |
| Necromancer's Quest Beta | metrics_json | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | gameplays_count_with_delimiter | 11137 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Necromancer's Quest Beta | metrics_json | `http://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | 3 |
| Necromancer's Quest Beta | metrics_json | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | 3 |
| Necromancer's Quest Beta | metrics_json | `http://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | 3 |
| Necromancer's Quest Beta | metrics_json | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | 3 |
| Necromancer's Quest Beta | metrics_json | `http://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | 3 |
| Necromancer's Quest Beta | metrics_json | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | `https://www.kongregate.com/games/ExperaGameStudio/necromancers-quest-beta/metrics.json` | 3 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`