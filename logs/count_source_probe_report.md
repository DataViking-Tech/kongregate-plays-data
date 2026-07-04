# Archived Count Source Probe

- Generated: 2026-07-04T02:04:58Z
- Target games: 32
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 7
- Endpoint candidates checked: 7
- Candidate observation rows: 7
- CDX status counts: fetched=7
- CDX rows found: 1
- Candidates with CDX rows: 1
- Payloads with count-like signals: 1
- Parsed play-count rows: 1
- Deduped recovered play-count observations: 785 (0 new this run)
- Accumulated probe-history rows: 18185 (7 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Mr.Vengeance: Upgrade | metrics_json | `https://www.kongregate.com/games/tmifx/mr-vengeance-upgrade/metrics.json` | `https://www.kongregate.com/games/tmifx/mr-vengeance-upgrade/metrics.json` | gameplays_count_with_delimiter | 43109 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Mr.Vengeance: Upgrade | metrics_json | `https://www.kongregate.com/games/tmifx/mr-vengeance-upgrade/metrics.json` | `https://www.kongregate.com/games/tmifx/mr-vengeance-upgrade/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`