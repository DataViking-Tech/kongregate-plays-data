# Archived Count Source Probe

- Generated: 2026-07-03T20:54:42Z
- Target games: 8
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 8
- Endpoint candidates checked: 16
- Candidate observation rows: 16
- CDX status counts: cached=5, fetched=11
- CDX rows found: 2
- Candidates with CDX rows: 2
- Payloads with count-like signals: 2
- Parsed play-count rows: 2
- Deduped recovered play-count observations: 624 (1 new this run)
- Accumulated probe-history rows: 15738 (13 new, 3 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Afterburner | metrics_json | `http://www.kongregate.com/games/zerodevider/afterburner/metrics.json` | `https://www.kongregate.com/games/zerodevider/afterburner/metrics.json` | gameplays_count_with_delimiter | 250 |
| Afterburner | metrics_json | `https://www.kongregate.com/games/zerodevider/afterburner/metrics.json` | `https://www.kongregate.com/games/zerodevider/afterburner/metrics.json` | gameplays_count_with_delimiter | 250 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Afterburner | metrics_json | `http://www.kongregate.com/games/zerodevider/afterburner/metrics.json` | `https://www.kongregate.com/games/zerodevider/afterburner/metrics.json` | 1 |
| Afterburner | metrics_json | `https://www.kongregate.com/games/zerodevider/afterburner/metrics.json` | `https://www.kongregate.com/games/zerodevider/afterburner/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`