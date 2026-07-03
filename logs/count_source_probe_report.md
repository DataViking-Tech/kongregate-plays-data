# Archived Count Source Probe

- Generated: 2026-07-03T12:08:19Z
- Target games: 3
- Status filter: transient_failures_remaining
- Games with cached archived pages: 3
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 3
- Candidate observation rows: 4
- CDX status counts: fetched=4
- CDX rows found: 10
- Candidates with CDX rows: 2
- Payloads with count-like signals: 2
- Parsed play-count rows: 2
- Deduped recovered play-count observations: 72 (2 new this run)
- Accumulated probe-history rows: 12792 (4 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Medieval Cop - Dregg Me To Hell | metrics_json | `http://www.kongregate.com/games/VasantJ/medieval-cop-dregg-me-to-hell/metrics.json` | `https://www.kongregate.com/games/VasantJ/medieval-cop-dregg-me-to-hell/metrics.json` | gameplays_count_with_delimiter | 145144 |
| Medieval Cop - Dregg Me To Hell | metrics_json | `http://www.kongregate.com/games/VasantJ/medieval-cop-dregg-me-to-hell/metrics.json` | `https://www.kongregate.com/games/VasantJ/medieval-cop-dregg-me-to-hell/metrics.json` | gameplays_count_with_delimiter | 144385 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Medieval Cop - Dregg Me To Hell | metrics_json | `http://www.kongregate.com/games/VasantJ/medieval-cop-dregg-me-to-hell/metrics.json` | `https://www.kongregate.com/games/VasantJ/medieval-cop-dregg-me-to-hell/metrics.json` | 5 |
| Medieval Cop - Dregg Me To Hell | metrics_json | `http://www.kongregate.com/games/VasantJ/medieval-cop-dregg-me-to-hell/metrics.json` | `https://www.kongregate.com/games/VasantJ/medieval-cop-dregg-me-to-hell/metrics.json` | 5 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`