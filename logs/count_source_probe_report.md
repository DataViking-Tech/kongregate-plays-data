# Archived Count Source Probe

- Generated: 2026-07-03T10:57:30Z
- Target games: 4
- Status filter: none
- Games with cached archived pages: 4
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 4
- Candidate observation rows: 4
- CDX status counts: fetched=4
- CDX rows found: 1
- Candidates with CDX rows: 1
- Payloads with count-like signals: 1
- Parsed play-count rows: 1
- Deduped recovered play-count observations: 7 (1 new this run)
- Accumulated probe-history rows: 12511 (4 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Battle Of Heroes | metrics_json | `http://www.kongregate.com/games/Andrew_Nyers/battle-of-heroes/metrics.json` | `http://www.kongregate.com/games/Andrew_Nyers/battle-of-heroes/metrics.json` | gameplays_count_with_delimiter | 57018 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Battle Of Heroes | metrics_json | `http://www.kongregate.com/games/Andrew_Nyers/battle-of-heroes/metrics.json` | `http://www.kongregate.com/games/Andrew_Nyers/battle-of-heroes/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`