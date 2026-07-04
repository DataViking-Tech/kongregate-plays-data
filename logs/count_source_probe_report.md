# Archived Count Source Probe

- Generated: 2026-07-04T05:08:44Z
- Target games: 32
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 14
- Endpoint candidates checked: 27
- Candidate observation rows: 27
- CDX status counts: failed=7, fetched=20
- CDX rows found: 2
- Candidates with CDX rows: 2
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 854 (0 new this run)
- Accumulated probe-history rows: 19735 (20 new, 7 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Heroes Tactics | metrics_json | `http://www.kongregate.com/games/heroestactics/heroes-tactics/metrics.json` | `http://www.kongregate.com/games/heroestactics/heroes-tactics/metrics.json` | 1 |
| Heroes Tactics | metrics_json | `https://www.kongregate.com/games/heroestactics/heroes-tactics/metrics.json` | `http://www.kongregate.com/games/heroestactics/heroes-tactics/metrics.json` | 1 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Retry Note

7 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`