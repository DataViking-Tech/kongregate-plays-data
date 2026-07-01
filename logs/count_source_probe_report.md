# Archived Count Source Probe

- Generated: 2026-07-01T13:33:09Z
- Target games: 1
- Status filter: transient_failures_remaining
- Games with cached archived pages: 1
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 12
- Candidate observation rows: 14
- CDX status counts: cached=13, fetched=1
- CDX rows found: 8
- Candidates with CDX rows: 4
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 1 (0 new this run)
- Accumulated probe-history rows: 1030 (14 new, 0 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| SUV Car Cartoon Puzzle | holodeck | `http://www.kongregate.com/games/natalibt/suv-car-cartoon-puzzle/holodeck` | `http://www.kongregate.com:80/games/natalibt/suv-car-cartoon-puzzle/holodeck` | 2 |
| SUV Car Cartoon Puzzle | holodeck | `http://www.kongregate.com/games/natalibt/suv-car-cartoon-puzzle/holodeck` | `http://www.kongregate.com:80/games/natalibt/suv-car-cartoon-puzzle/holodeck` | 2 |
| SUV Car Cartoon Puzzle | holodeck | `https://www.kongregate.com/games/natalibt/suv-car-cartoon-puzzle/holodeck` | `http://www.kongregate.com:80/games/natalibt/suv-car-cartoon-puzzle/holodeck` | 2 |
| SUV Car Cartoon Puzzle | holodeck | `https://www.kongregate.com/games/natalibt/suv-car-cartoon-puzzle/holodeck` | `http://www.kongregate.com:80/games/natalibt/suv-car-cartoon-puzzle/holodeck` | 2 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`