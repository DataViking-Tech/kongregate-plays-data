# Archived Count Source Probe

- Generated: 2026-07-01T21:27:12Z
- Target games: 3
- Status filter: transient_failures_remaining
- Games with cached archived pages: 2
- Games direct-probed from catalog URLs: 1
- Endpoint candidates checked: 36
- Candidate observation rows: 36
- CDX status counts: cached=32, fetched=4
- CDX rows found: 2
- Candidates with CDX rows: 2
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 1 (0 new this run)
- Accumulated probe-history rows: 5960 (27 new, 9 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Miner 2 | holodeck | `http://www.kongregate.com/games/KillingPigs123/miner-2/holodeck` | `http://www.kongregate.com:80/games/KillingPigs123/miner-2/holodeck` | 1 |
| Miner 2 | holodeck | `https://www.kongregate.com/games/KillingPigs123/miner-2/holodeck` | `http://www.kongregate.com:80/games/KillingPigs123/miner-2/holodeck` | 1 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`