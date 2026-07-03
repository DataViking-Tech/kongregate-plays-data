# Archived Count Source Probe

- Generated: 2026-07-03T14:52:25Z
- Target games: 5
- Status filter: none
- Games with cached archived pages: 5
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 20
- Candidate observation rows: 20
- CDX status counts: cached=10, fetched=10
- CDX rows found: 2
- Candidates with CDX rows: 2
- Payloads with count-like signals: 2
- Parsed play-count rows: 2
- Deduped recovered play-count observations: 99 (1 new this run)
- Accumulated probe-history rows: 13096 (20 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Space Defender YM | metrics_json | `http://www.kongregate.com/games/Yellowmen_Kit/space-defender-ym/metrics.json` | `https://www.kongregate.com/games/Yellowmen_Kit/space-defender-ym/metrics.json` | gameplays_count_with_delimiter | 180 |
| Space Defender YM | metrics_json | `https://www.kongregate.com/games/Yellowmen_Kit/space-defender-ym/metrics.json` | `https://www.kongregate.com/games/Yellowmen_Kit/space-defender-ym/metrics.json` | gameplays_count_with_delimiter | 180 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Space Defender YM | metrics_json | `http://www.kongregate.com/games/Yellowmen_Kit/space-defender-ym/metrics.json` | `https://www.kongregate.com/games/Yellowmen_Kit/space-defender-ym/metrics.json` | 1 |
| Space Defender YM | metrics_json | `https://www.kongregate.com/games/Yellowmen_Kit/space-defender-ym/metrics.json` | `https://www.kongregate.com/games/Yellowmen_Kit/space-defender-ym/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`