# Archived Count Source Probe

- Generated: 2026-07-03T21:20:45Z
- Target games: 1
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 1
- Endpoint candidates checked: 2
- Candidate observation rows: 8
- CDX status counts: cached=4, fetched=4
- CDX rows found: 32
- Candidates with CDX rows: 8
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 637 (0 new this run)
- Accumulated probe-history rows: 15958 (8 new, 0 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Space Bunny | metrics_json | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | 4 |
| Space Bunny | metrics_json | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | 4 |
| Space Bunny | metrics_json | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | 4 |
| Space Bunny | metrics_json | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | 4 |
| Space Bunny | metrics_json | `https://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | 4 |
| Space Bunny | metrics_json | `https://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | 4 |
| Space Bunny | metrics_json | `https://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | 4 |
| Space Bunny | metrics_json | `https://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | `http://www.kongregate.com/games/catsito001/space-bunny/metrics.json` | 4 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`