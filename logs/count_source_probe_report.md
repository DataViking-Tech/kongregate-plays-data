# Archived Count Source Probe

- Generated: 2026-07-03T14:06:00Z
- Target games: 5
- Status filter: none
- Games with cached archived pages: 5
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 18
- Candidate observation rows: 18
- CDX status counts: cached=8, fetched=10
- CDX rows found: 6
- Candidates with CDX rows: 6
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 81 (0 new this run)
- Accumulated probe-history rows: 13011 (18 new, 0 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Adam and Eve 2 | metrics_json | `http://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | `http://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | 1 |
| Adam and Eve 2 | metrics_json | `http://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | `http://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | 1 |
| Adam and Eve 2 | metrics_json | `http://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | `http://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | 1 |
| Adam and Eve 2 | metrics_json | `https://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | `http://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | 1 |
| Adam and Eve 2 | metrics_json | `https://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | `http://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | 1 |
| Adam and Eve 2 | metrics_json | `https://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | `http://www.kongregate.com/games/fastgames/adam-and-eve-2/metrics.json` | 1 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`