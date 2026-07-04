# Archived Count Source Probe

- Generated: 2026-07-04T01:38:26Z
- Target games: 32
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 5
- Endpoint candidates checked: 8
- Candidate observation rows: 8
- CDX status counts: fetched=8
- CDX rows found: 0
- Candidates with CDX rows: 0
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 778 (0 new this run)
- Accumulated probe-history rows: 17963 (8 new, 0 refreshed)

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`