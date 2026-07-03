# Archived Count Source Probe

- Generated: 2026-07-03T20:42:46Z
- Target games: 7
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 7
- Endpoint candidates checked: 14
- Candidate observation rows: 16
- CDX status counts: cached=2, fetched=14
- CDX rows found: 8
- Candidates with CDX rows: 4
- Payloads with count-like signals: 4
- Parsed play-count rows: 4
- Deduped recovered play-count observations: 622 (2 new this run)
- Accumulated probe-history rows: 15637 (16 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Feed The D (Christian-Friendly) | metrics_json | `http://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | gameplays_count_with_delimiter | 304 |
| Feed The D (Christian-Friendly) | metrics_json | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | gameplays_count_with_delimiter | 304 |
| Feed The D (Christian-Friendly) | metrics_json | `http://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | gameplays_count_with_delimiter | 296 |
| Feed The D (Christian-Friendly) | metrics_json | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | gameplays_count_with_delimiter | 296 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Feed The D (Christian-Friendly) | metrics_json | `http://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | 2 |
| Feed The D (Christian-Friendly) | metrics_json | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | 2 |
| Feed The D (Christian-Friendly) | metrics_json | `http://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | 2 |
| Feed The D (Christian-Friendly) | metrics_json | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | `https://www.kongregate.com/games/AnAlt_Ver3/feed-the-d-christian-friendly/metrics.json` | 2 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`