# Archived Count Source Probe

- Generated: 2026-07-03T22:44:04Z
- Target games: 1
- Status filter: transient_failures_remaining
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 1
- Endpoint candidates checked: 1
- Candidate observation rows: 1
- CDX status counts: fetched=1
- CDX rows found: 1
- Candidates with CDX rows: 1
- Payloads with count-like signals: 1
- Parsed play-count rows: 1
- Deduped recovered play-count observations: 690 (1 new this run)
- Accumulated probe-history rows: 16632 (1 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| R-G-B | metrics_json | `http://www.kongregate.com/games/AttalK/r-g-b/metrics.json` | `https://www.kongregate.com/games/AttalK/r-g-b/metrics.json` | gameplays_count_with_delimiter | 71 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| R-G-B | metrics_json | `http://www.kongregate.com/games/AttalK/r-g-b/metrics.json` | `https://www.kongregate.com/games/AttalK/r-g-b/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`