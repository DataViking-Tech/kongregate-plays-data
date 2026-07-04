# Archived Count Source Probe

- Generated: 2026-07-04T05:20:08Z
- Target games: 32
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 17
- Endpoint candidates checked: 31
- Candidate observation rows: 33
- CDX status counts: failed=9, fetched=24
- CDX rows found: 12
- Candidates with CDX rows: 4
- Payloads with count-like signals: 3
- Parsed play-count rows: 3
- Deduped recovered play-count observations: 861 (2 new this run)
- Accumulated probe-history rows: 19848 (24 new, 9 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Splitter 2 | metrics_json | `https://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | `https://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | gameplays_count_with_delimiter | 3335340 |
| Splitter 2 | metrics_json | `http://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | `http://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | gameplays_count_with_delimiter | 3332734 |
| Splitter 2 | metrics_json | `https://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | `http://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | gameplays_count_with_delimiter | 3332734 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Splitter 2 | metrics_json | `https://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | `https://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | 3 |
| Splitter 2 | metrics_json | `http://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | `http://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | 3 |
| Splitter 2 | metrics_json | `https://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | `http://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | 3 |
| Splitter 2 | metrics_json | `http://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | `https://www.kongregate.com/games/CasualCollective/splitter-2/metrics.json` | 3 |

## Retry Note

9 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`