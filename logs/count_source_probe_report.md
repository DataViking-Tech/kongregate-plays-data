# Archived Count Source Probe

- Generated: 2026-07-01T10:07:19Z
- Target games: 8
- Games with cached archived pages: 8
- Endpoint candidates checked: 88
- CDX status counts: cached=38, failed=31, fetched=19
- CDX rows found: 0
- Candidates with CDX rows: 0
- Payloads with count-like signals: 0
- Parsed play-count rows: 0

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Retry Note

31 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `logs/count_source_probe_report.json`