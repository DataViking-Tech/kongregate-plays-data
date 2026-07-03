# Archived Count Source Probe

- Generated: 2026-07-03T18:39:36Z
- Target games: 6
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 6
- Endpoint candidates checked: 12
- Candidate observation rows: 12
- CDX status counts: cached=3, fetched=9
- CDX rows found: 0
- Candidates with CDX rows: 0
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 584 (0 new this run)
- Accumulated probe-history rows: 14907 (12 new, 0 refreshed)

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`