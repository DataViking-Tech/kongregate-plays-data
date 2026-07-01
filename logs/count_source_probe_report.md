# Archived Count Source Probe

- Generated: 2026-07-01T11:27:24Z
- Target games: 1
- Games with cached archived pages: 1
- Endpoint candidates checked: 12
- CDX status counts: cached=12
- CDX rows found: 168
- Candidates with CDX rows: 12
- Payloads with count-like signals: 8
- Parsed play-count rows: 2
- Deduped recovered play-count observations: 1 (0 new this run)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| SuperBall Idle | game_path_prefix | `http://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2/metrics.json` | gameplays_count_with_delimiter | 3734 |
| SuperBall Idle | game_path_prefix | `https://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2/metrics.json` | gameplays_count_with_delimiter | 3734 |
| SuperBall Idle | game_path_prefix | `http://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com:80/games/joao8991/superball-idle` | gameplays_count | n/a |
| SuperBall Idle | game_path_prefix | `http://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com:80/games/joao8991/superball-idle-2` | gameplays_count | n/a |
| SuperBall Idle | game_path_prefix | `http://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2` | gameplays_count | n/a |
| SuperBall Idle | game_path_prefix | `https://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com:80/games/joao8991/superball-idle` | gameplays_count | n/a |
| SuperBall Idle | game_path_prefix | `https://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com:80/games/joao8991/superball-idle-2` | gameplays_count | n/a |
| SuperBall Idle | game_path_prefix | `https://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2` | gameplays_count | n/a |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| SuperBall Idle | game_path_prefix | `http://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2/metrics.json` | 14 |
| SuperBall Idle | game_path_prefix | `https://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2/metrics.json` | 14 |
| SuperBall Idle | game_path_prefix | `http://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com:80/games/joao8991/superball-idle` | 14 |
| SuperBall Idle | game_path_prefix | `http://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com:80/games/joao8991/superball-idle-2` | 14 |
| SuperBall Idle | game_path_prefix | `http://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2` | 14 |
| SuperBall Idle | game_path_prefix | `https://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com:80/games/joao8991/superball-idle` | 14 |
| SuperBall Idle | game_path_prefix | `https://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com:80/games/joao8991/superball-idle-2` | 14 |
| SuperBall Idle | game_path_prefix | `https://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2` | 14 |
| SuperBall Idle | game_path_prefix | `http://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2/holodeck` | 14 |
| SuperBall Idle | game_path_prefix | `http://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2/show_below_fold` | 14 |
| SuperBall Idle | game_path_prefix | `https://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2/holodeck` | 14 |
| SuperBall Idle | game_path_prefix | `https://www.kongregate.com/games/joao8991/superball-idle` | `http://www.kongregate.com/games/joao8991/superball-idle-2/show_below_fold` | 14 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`