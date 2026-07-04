# Archived Count Source Probe

- Generated: 2026-07-04T03:35:39Z
- Target games: 32
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 15
- Endpoint candidates checked: 27
- Candidate observation rows: 27
- CDX status counts: failed=6, fetched=21
- CDX rows found: 1
- Candidates with CDX rows: 1
- Payloads with count-like signals: 1
- Parsed play-count rows: 1
- Deduped recovered play-count observations: 814 (0 new this run)
- Accumulated probe-history rows: 19061 (21 new, 6 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Hexa_Match | metrics_json | `https://www.kongregate.com/games/PasKuda13/hexa-match/metrics.json` | `https://www.kongregate.com/games/PasKuda13/hexa-match/metrics.json` | gameplays_count_with_delimiter | 1017 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Hexa_Match | metrics_json | `https://www.kongregate.com/games/PasKuda13/hexa-match/metrics.json` | `https://www.kongregate.com/games/PasKuda13/hexa-match/metrics.json` | 1 |

## Retry Note

6 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`