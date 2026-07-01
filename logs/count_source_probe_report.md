# Archived Count Source Probe

- Generated: 2026-07-01T11:44:52Z
- Target games: 4
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 4
- Endpoint candidates checked: 48
- Candidate observation rows: 48
- CDX status counts: cached=27, failed=15, fetched=6
- CDX rows found: 0
- Candidates with CDX rows: 0
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 1 (0 new this run)

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Retry Note

15 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`