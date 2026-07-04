# Archived Count Source Probe

- Generated: 2026-07-04T00:13:16Z
- Target games: 9
- Status filter: transient_failures_remaining
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 9
- Endpoint candidates checked: 16
- Candidate observation rows: 16
- CDX status counts: fetched=16
- CDX rows found: 4
- Candidates with CDX rows: 4
- Payloads with count-like signals: 4
- Parsed play-count rows: 4
- Deduped recovered play-count observations: 724 (2 new this run)
- Accumulated probe-history rows: 17349 (16 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| When the Lights Go Down | metrics_json | `http://www.kongregate.com/games/dragonlance5/when-the-lights-go-down/metrics.json` | `https://www.kongregate.com/games/dragonlance5/when-the-lights-go-down/metrics.json` | gameplays_count_with_delimiter | 147 |
| When the Lights Go Down | metrics_json | `https://www.kongregate.com/games/dragonlance5/when-the-lights-go-down/metrics.json` | `https://www.kongregate.com/games/dragonlance5/when-the-lights-go-down/metrics.json` | gameplays_count_with_delimiter | 147 |
| Obversum | metrics_json | `http://www.kongregate.com/games/mmongeon/obversum/metrics.json` | `https://www.kongregate.com/games/mmongeon/obversum/metrics.json` | gameplays_count_with_delimiter | 135 |
| Obversum | metrics_json | `https://www.kongregate.com/games/mmongeon/obversum/metrics.json` | `https://www.kongregate.com/games/mmongeon/obversum/metrics.json` | gameplays_count_with_delimiter | 135 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| When the Lights Go Down | metrics_json | `http://www.kongregate.com/games/dragonlance5/when-the-lights-go-down/metrics.json` | `https://www.kongregate.com/games/dragonlance5/when-the-lights-go-down/metrics.json` | 1 |
| When the Lights Go Down | metrics_json | `https://www.kongregate.com/games/dragonlance5/when-the-lights-go-down/metrics.json` | `https://www.kongregate.com/games/dragonlance5/when-the-lights-go-down/metrics.json` | 1 |
| Obversum | metrics_json | `http://www.kongregate.com/games/mmongeon/obversum/metrics.json` | `https://www.kongregate.com/games/mmongeon/obversum/metrics.json` | 1 |
| Obversum | metrics_json | `https://www.kongregate.com/games/mmongeon/obversum/metrics.json` | `https://www.kongregate.com/games/mmongeon/obversum/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`