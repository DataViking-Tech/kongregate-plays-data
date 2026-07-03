# Archived Count Source Probe

- Generated: 2026-07-03T13:57:22Z
- Target games: 4
- Status filter: none
- Games with cached archived pages: 4
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 16
- Candidate observation rows: 16
- CDX status counts: cached=16
- CDX rows found: 0
- Candidates with CDX rows: 0
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 81 (0 new this run)
- Accumulated probe-history rows: 12993 (8 new, 8 refreshed)

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`