# Archived Count Source Probe

- Generated: 2026-07-04T04:52:37Z
- Target games: 32
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 16
- Endpoint candidates checked: 31
- Candidate observation rows: 31
- CDX status counts: failed=11, fetched=20
- CDX rows found: 4
- Candidates with CDX rows: 4
- Payloads with count-like signals: 4
- Parsed play-count rows: 4
- Deduped recovered play-count observations: 852 (2 new this run)
- Accumulated probe-history rows: 19632 (20 new, 11 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Nuke Gun | metrics_json | `http://www.kongregate.com/games/kizigames/nuke-gun/metrics.json` | `http://www.kongregate.com/games/kizigames/nuke-gun/metrics.json` | gameplays_count_with_delimiter | 49072 |
| Nuke Gun | metrics_json | `https://www.kongregate.com/games/kizigames/nuke-gun/metrics.json` | `http://www.kongregate.com/games/kizigames/nuke-gun/metrics.json` | gameplays_count_with_delimiter | 49072 |
| Promise Keepers | metrics_json | `http://www.kongregate.com/games/SandraKim/promise-keepers/metrics.json` | `https://www.kongregate.com/games/SandraKim/promise-keepers/metrics.json` | gameplays_count_with_delimiter | 65 |
| Promise Keepers | metrics_json | `https://www.kongregate.com/games/SandraKim/promise-keepers/metrics.json` | `https://www.kongregate.com/games/SandraKim/promise-keepers/metrics.json` | gameplays_count_with_delimiter | 65 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Nuke Gun | metrics_json | `http://www.kongregate.com/games/kizigames/nuke-gun/metrics.json` | `http://www.kongregate.com/games/kizigames/nuke-gun/metrics.json` | 1 |
| Nuke Gun | metrics_json | `https://www.kongregate.com/games/kizigames/nuke-gun/metrics.json` | `http://www.kongregate.com/games/kizigames/nuke-gun/metrics.json` | 1 |
| Promise Keepers | metrics_json | `http://www.kongregate.com/games/SandraKim/promise-keepers/metrics.json` | `https://www.kongregate.com/games/SandraKim/promise-keepers/metrics.json` | 1 |
| Promise Keepers | metrics_json | `https://www.kongregate.com/games/SandraKim/promise-keepers/metrics.json` | `https://www.kongregate.com/games/SandraKim/promise-keepers/metrics.json` | 1 |

## Retry Note

11 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`