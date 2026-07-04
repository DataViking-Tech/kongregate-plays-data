# Archived Count Source Probe

- Generated: 2026-07-04T05:34:40Z
- Target games: 32
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 14
- Endpoint candidates checked: 26
- Candidate observation rows: 28
- CDX status counts: failed=7, fetched=21
- CDX rows found: 12
- Candidates with CDX rows: 8
- Payloads with count-like signals: 8
- Parsed play-count rows: 8
- Deduped recovered play-count observations: 867 (4 new this run)
- Accumulated probe-history rows: 19947 (21 new, 7 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Spaceship Shooter | metrics_json | `http://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | `https://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | gameplays_count_with_delimiter | 8708 |
| Spaceship Shooter | metrics_json | `https://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | `https://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | gameplays_count_with_delimiter | 8708 |
| Spaceship Shooter | metrics_json | `http://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | `http://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | gameplays_count_with_delimiter | 8659 |
| Spaceship Shooter | metrics_json | `https://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | `http://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | gameplays_count_with_delimiter | 8659 |
| school project 3d forrest | metrics_json | `http://www.kongregate.com/games/mynameisxboard/school-project-3d-forrest/metrics.json` | `https://www.kongregate.com/games/mynameisxboard/school-project-3d-forrest/metrics.json` | gameplays_count_with_delimiter | 312 |
| school project 3d forrest | metrics_json | `https://www.kongregate.com/games/mynameisxboard/school-project-3d-forrest/metrics.json` | `https://www.kongregate.com/games/mynameisxboard/school-project-3d-forrest/metrics.json` | gameplays_count_with_delimiter | 312 |
| sCHOOL | metrics_json | `http://www.kongregate.com/games/Iam_GamerPS5/school/metrics.json` | `http://www.kongregate.com/games/Iam_GamerPS5/school/metrics.json` | gameplays_count_with_delimiter | 61 |
| sCHOOL | metrics_json | `https://www.kongregate.com/games/Iam_GamerPS5/school/metrics.json` | `http://www.kongregate.com/games/Iam_GamerPS5/school/metrics.json` | gameplays_count_with_delimiter | 61 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Spaceship Shooter | metrics_json | `http://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | `https://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | 2 |
| Spaceship Shooter | metrics_json | `https://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | `https://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | 2 |
| Spaceship Shooter | metrics_json | `http://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | `http://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | 2 |
| Spaceship Shooter | metrics_json | `https://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | `http://www.kongregate.com/games/kizigames/spaceship-shooter/metrics.json` | 2 |
| school project 3d forrest | metrics_json | `http://www.kongregate.com/games/mynameisxboard/school-project-3d-forrest/metrics.json` | `https://www.kongregate.com/games/mynameisxboard/school-project-3d-forrest/metrics.json` | 1 |
| school project 3d forrest | metrics_json | `https://www.kongregate.com/games/mynameisxboard/school-project-3d-forrest/metrics.json` | `https://www.kongregate.com/games/mynameisxboard/school-project-3d-forrest/metrics.json` | 1 |
| sCHOOL | metrics_json | `http://www.kongregate.com/games/Iam_GamerPS5/school/metrics.json` | `http://www.kongregate.com/games/Iam_GamerPS5/school/metrics.json` | 1 |
| sCHOOL | metrics_json | `https://www.kongregate.com/games/Iam_GamerPS5/school/metrics.json` | `http://www.kongregate.com/games/Iam_GamerPS5/school/metrics.json` | 1 |

## Retry Note

7 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`