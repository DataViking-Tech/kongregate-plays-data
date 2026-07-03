# Archived Count Source Probe

- Generated: 2026-07-03T22:17:34Z
- Target games: 12
- Status filter: transient_failures_remaining
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 12
- Endpoint candidates checked: 15
- Candidate observation rows: 15
- CDX status counts: fetched=15
- CDX rows found: 1
- Candidates with CDX rows: 1
- Payloads with count-like signals: 1
- Parsed play-count rows: 1
- Deduped recovered play-count observations: 685 (1 new this run)
- Accumulated probe-history rows: 16429 (15 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| The depths idle | metrics_json | `http://www.kongregate.com/games/omgnoob191/the-depths-idle/metrics.json` | `https://www.kongregate.com/games/omgnoob191/the-depths-idle/metrics.json` | gameplays_count_with_delimiter | 265969 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| The depths idle | metrics_json | `http://www.kongregate.com/games/omgnoob191/the-depths-idle/metrics.json` | `https://www.kongregate.com/games/omgnoob191/the-depths-idle/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`