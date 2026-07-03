# Archived Count Source Probe

- Generated: 2026-07-03T11:45:03Z
- Target games: 5
- Status filter: none
- Games with cached archived pages: 5
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 5
- Candidate observation rows: 5
- CDX status counts: fetched=5
- CDX rows found: 1
- Candidates with CDX rows: 1
- Payloads with count-like signals: 1
- Parsed play-count rows: 1
- Deduped recovered play-count observations: 37 (1 new this run)
- Accumulated probe-history rows: 12739 (5 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Jellydad Hero | metrics_json | `http://www.kongregate.com/games/PITon_/jellydad-hero/metrics.json` | `http://www.kongregate.com/games/PITon_/jellydad-hero/metrics.json` | gameplays_count_with_delimiter | 31610 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Jellydad Hero | metrics_json | `http://www.kongregate.com/games/PITon_/jellydad-hero/metrics.json` | `http://www.kongregate.com/games/PITon_/jellydad-hero/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`