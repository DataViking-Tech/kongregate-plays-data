# Archived Count Source Probe

- Generated: 2026-07-03T23:59:44Z
- Target games: 9
- Status filter: transient_failures_remaining
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 9
- Endpoint candidates checked: 14
- Candidate observation rows: 14
- CDX status counts: fetched=14
- CDX rows found: 2
- Candidates with CDX rows: 2
- Payloads with count-like signals: 2
- Parsed play-count rows: 2
- Deduped recovered play-count observations: 722 (1 new this run)
- Accumulated probe-history rows: 17250 (14 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Volcano Idols | metrics_json | `http://www.kongregate.com/games/laFunk/volcano-idols/metrics.json` | `https://www.kongregate.com/games/laFunk/volcano-idols/metrics.json` | gameplays_count_with_delimiter | 746 |
| Volcano Idols | metrics_json | `https://www.kongregate.com/games/laFunk/volcano-idols/metrics.json` | `https://www.kongregate.com/games/laFunk/volcano-idols/metrics.json` | gameplays_count_with_delimiter | 746 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Volcano Idols | metrics_json | `http://www.kongregate.com/games/laFunk/volcano-idols/metrics.json` | `https://www.kongregate.com/games/laFunk/volcano-idols/metrics.json` | 1 |
| Volcano Idols | metrics_json | `https://www.kongregate.com/games/laFunk/volcano-idols/metrics.json` | `https://www.kongregate.com/games/laFunk/volcano-idols/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`