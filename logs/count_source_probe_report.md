# Archived Count Source Probe

- Generated: 2026-07-03T11:13:32Z
- Target games: 4
- Status filter: transient_failures_remaining
- Games with cached archived pages: 3
- Games direct-probed from catalog URLs: 1
- Endpoint candidates checked: 4
- Candidate observation rows: 7
- CDX status counts: fetched=7
- CDX rows found: 190
- Candidates with CDX rows: 6
- Payloads with count-like signals: 6
- Parsed play-count rows: 6
- Deduped recovered play-count observations: 36 (6 new this run)
- Accumulated probe-history rows: 12550 (7 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Fleeing the Complex | metrics_json | `http://www.kongregate.com/games/Puffballs_United/fleeing-the-complex/metrics.json` | `https://www.kongregate.com/games/Puffballs_United/fleeing-the-complex/metrics.json` | gameplays_count_with_delimiter | 1364806 |
| There is no game | metrics_json | `http://www.kongregate.com/games/KaMiZoTo_Creator/there-is-no-game/metrics.json` | `https://www.kongregate.com/games/KaMiZoTo_Creator/there-is-no-game/metrics.json` | gameplays_count_with_delimiter | 1180233 |
| Fleeing the Complex | metrics_json | `http://www.kongregate.com/games/Puffballs_United/fleeing-the-complex/metrics.json` | `http://www.kongregate.com:80/games/Puffballs_United/fleeing-the-complex/metrics.json` | gameplays_count_with_delimiter | 1107903 |
| There is no game | metrics_json | `http://www.kongregate.com/games/KaMiZoTo_Creator/there-is-no-game/metrics.json` | `http://www.kongregate.com/games/KaMiZoTo_Creator/there-is-no-game/metrics.json` | gameplays_count_with_delimiter | 743305 |
| Incremancer | metrics_json | `http://www.kongregate.com/games/JamesG466/incremancer/metrics.json` | `https://www.kongregate.com/games/JamesG466/incremancer/metrics.json` | gameplays_count_with_delimiter | 364493 |
| Incremancer | metrics_json | `http://www.kongregate.com/games/JamesG466/incremancer/metrics.json` | `https://www.kongregate.com/games/JamesG466/incremancer/metrics.json` | gameplays_count_with_delimiter | 227819 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Fleeing the Complex | metrics_json | `http://www.kongregate.com/games/Puffballs_United/fleeing-the-complex/metrics.json` | `https://www.kongregate.com/games/Puffballs_United/fleeing-the-complex/metrics.json` | 27 |
| There is no game | metrics_json | `http://www.kongregate.com/games/KaMiZoTo_Creator/there-is-no-game/metrics.json` | `https://www.kongregate.com/games/KaMiZoTo_Creator/there-is-no-game/metrics.json` | 20 |
| Fleeing the Complex | metrics_json | `http://www.kongregate.com/games/Puffballs_United/fleeing-the-complex/metrics.json` | `http://www.kongregate.com:80/games/Puffballs_United/fleeing-the-complex/metrics.json` | 27 |
| There is no game | metrics_json | `http://www.kongregate.com/games/KaMiZoTo_Creator/there-is-no-game/metrics.json` | `http://www.kongregate.com/games/KaMiZoTo_Creator/there-is-no-game/metrics.json` | 20 |
| Incremancer | metrics_json | `http://www.kongregate.com/games/JamesG466/incremancer/metrics.json` | `https://www.kongregate.com/games/JamesG466/incremancer/metrics.json` | 48 |
| Incremancer | metrics_json | `http://www.kongregate.com/games/JamesG466/incremancer/metrics.json` | `https://www.kongregate.com/games/JamesG466/incremancer/metrics.json` | 48 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`