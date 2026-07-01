# Archived Count Source Probe

- Generated: 2026-07-01T18:46:22Z
- Target games: 3
- Status filter: transient_failures_remaining
- Games with cached archived pages: 1
- Games direct-probed from catalog URLs: 2
- Endpoint candidates checked: 36
- Candidate observation rows: 36
- CDX status counts: cached=33, fetched=3
- CDX rows found: 2
- Candidates with CDX rows: 2
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 1 (0 new this run)
- Accumulated probe-history rows: 4097 (21 new, 15 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Crazy Zombie v2.0 Crossing Hero | holodeck | `http://www.kongregate.com/games/game4joy/crazy-zombie-v2-0-crossing-hero/holodeck` | `http://www.kongregate.com:80/games/game4joy/crazy-zombie-v2-0-crossing-hero/holodeck` | 1 |
| Crazy Zombie v2.0 Crossing Hero | holodeck | `https://www.kongregate.com/games/game4joy/crazy-zombie-v2-0-crossing-hero/holodeck` | `http://www.kongregate.com:80/games/game4joy/crazy-zombie-v2-0-crossing-hero/holodeck` | 1 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`