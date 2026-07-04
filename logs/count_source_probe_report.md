# Archived Count Source Probe

- Generated: 2026-07-04T03:22:33Z
- Target games: 32
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 14
- Endpoint candidates checked: 25
- Candidate observation rows: 27
- CDX status counts: failed=7, fetched=20
- CDX rows found: 36
- Candidates with CDX rows: 4
- Payloads with count-like signals: 4
- Parsed play-count rows: 4
- Deduped recovered play-count observations: 813 (2 new this run)
- Accumulated probe-history rows: 18958 (20 new, 7 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Midas' Gold Plus | metrics_json | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | gameplays_count_with_delimiter | 2360884 |
| Midas' Gold Plus | metrics_json | `https://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | gameplays_count_with_delimiter | 2360884 |
| Midas' Gold Plus | metrics_json | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | gameplays_count_with_delimiter | 470319 |
| Midas' Gold Plus | metrics_json | `https://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | gameplays_count_with_delimiter | 470319 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Midas' Gold Plus | metrics_json | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | 9 |
| Midas' Gold Plus | metrics_json | `https://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | 9 |
| Midas' Gold Plus | metrics_json | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | 9 |
| Midas' Gold Plus | metrics_json | `https://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | `http://www.kongregate.com/games/HolydayStudios/midas-gold-plus/metrics.json` | 9 |

## Retry Note

7 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`