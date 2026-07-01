# Archived Count Source Probe

- Generated: 2026-07-01T19:35:24Z
- Target games: 4
- Status filter: transient_failures_remaining
- Games with cached archived pages: 1
- Games direct-probed from catalog URLs: 3
- Endpoint candidates checked: 48
- Candidate observation rows: 48
- CDX status counts: cached=30, fetched=18
- CDX rows found: 0
- Candidates with CDX rows: 0
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 1 (0 new this run)
- Accumulated probe-history rows: 4651 (43 new, 5 refreshed)

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`