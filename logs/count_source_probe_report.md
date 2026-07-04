# Archived Count Source Probe

- Generated: 2026-07-04T04:13:46Z
- Target games: 32
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 12
- Endpoint candidates checked: 19
- Candidate observation rows: 19
- CDX status counts: failed=3, fetched=16
- CDX rows found: 0
- Candidates with CDX rows: 0
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 824 (0 new this run)
- Accumulated probe-history rows: 19288 (16 new, 3 refreshed)

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Retry Note

3 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`