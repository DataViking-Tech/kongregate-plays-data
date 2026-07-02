# Archived Count Source Probe

- Generated: 2026-07-02T00:19:29Z
- Target games: 6
- Status filter: transient_failures_remaining
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 6
- Endpoint candidates checked: 52
- Candidate observation rows: 52
- CDX status counts: cached=18, fetched=34
- CDX rows found: 2
- Candidates with CDX rows: 2
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 1 (0 new this run)
- Accumulated probe-history rows: 7846 (52 new, 0 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Quantum Of Light | holodeck | `http://www.kongregate.com/games/foumart/quantum-of-light/holodeck` | `http://www.kongregate.com/games/foumart/quantum-of-light/holodeck` | 1 |
| Quantum Of Light | holodeck | `https://www.kongregate.com/games/foumart/quantum-of-light/holodeck` | `http://www.kongregate.com/games/foumart/quantum-of-light/holodeck` | 1 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`