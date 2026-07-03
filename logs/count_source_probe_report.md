# Archived Count Source Probe

- Generated: 2026-07-03T16:39:48Z
- Target games: 2
- Status filter: none
- Games with cached archived pages: 2
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 64
- Candidate observation rows: 92
- CDX status counts: cached=59, failed=11, fetched=22
- CDX rows found: 2862
- Candidates with CDX rows: 42
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 405 (0 new this run)
- Accumulated probe-history rows: 14425 (92 new, 0 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Bad Eggs Online 2 | holodeck | `http://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `http://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `http://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `http://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `http://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `http://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `http://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `http://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `http://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `https://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `https://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `https://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `https://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `https://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `https://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `https://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `https://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Bad Eggs Online 2 | holodeck | `https://www.kongregate.com/games/Rob_Almighty/bad-eggs-online-2/holodeck` | `http://www.kongregate.com:80/games/Rob_Almighty/bad-eggs-online-2/holodeck` | 75 |
| Game of Thrones Ascent | holodeck | `http://www.kongregate.com/games/DisruptorBeam/game-of-thrones-ascent/holodeck` | `http://www.kongregate.com/games/DisruptorBeam/game-of-thrones-ascent/holodeck` | 63 |
| Game of Thrones Ascent | holodeck | `http://www.kongregate.com/games/DisruptorBeam/game-of-thrones-ascent/holodeck` | `http://www.kongregate.com/games/DisruptorBeam/game-of-thrones-ascent/holodeck` | 63 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Retry Note

11 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`