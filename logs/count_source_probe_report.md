# Archived Count Source Probe

- Generated: 2026-07-04T08:23:56Z
- Target games: 12
- Status filter: none
- Games with cached archived pages: 12
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 80
- Candidate observation rows: 84
- CDX status counts: cached=4, failed=76, fetched=4
- CDX rows found: 800
- Candidates with CDX rows: 8
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 645 (0 new this run)
- Accumulated probe-history rows: 21181 (74 new, 10 refreshed)
- Stopped after CDX lookup cap: 80

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Supermechs | holodeck | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | 100 |
| Supermechs | holodeck | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | 100 |
| Supermechs | holodeck | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | 100 |
| Supermechs | holodeck | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | 100 |
| Supermechs | holodeck | `https://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | 100 |
| Supermechs | holodeck | `https://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | 100 |
| Supermechs | holodeck | `https://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | 100 |
| Supermechs | holodeck | `https://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | `http://www.kongregate.com/games/Tacticsoft/supermechs/holodeck` | 100 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Retry Note

76 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`