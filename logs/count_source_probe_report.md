# Archived Count Source Probe

- Generated: 2026-07-03T21:48:52Z
- Target games: 11
- Status filter: none
- Games with cached archived pages: 1
- Games direct-probed from catalog URLs: 10
- Endpoint candidates checked: 28
- Candidate observation rows: 28
- CDX status counts: cached=11, fetched=17
- CDX rows found: 2
- Candidates with CDX rows: 2
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 669 (0 new this run)
- Accumulated probe-history rows: 16218 (24 new, 4 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| The Swordman | metrics_json | `http://www.kongregate.com/games/TheGameFather/the-swordman/metrics.json` | `http://www.kongregate.com/games/TheGameFather/the-swordman/metrics.json` | 1 |
| The Swordman | metrics_json | `https://www.kongregate.com/games/TheGameFather/the-swordman/metrics.json` | `http://www.kongregate.com/games/TheGameFather/the-swordman/metrics.json` | 1 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`