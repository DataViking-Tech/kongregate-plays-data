# Archived Count Source Probe

- Generated: 2026-07-03T12:51:50Z
- Target games: 7
- Status filter: none
- Games with cached archived pages: 7
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 22
- Candidate observation rows: 22
- CDX status counts: cached=8, fetched=14
- CDX rows found: 6
- Candidates with CDX rows: 6
- Payloads with count-like signals: 6
- Parsed play-count rows: 6
- Deduped recovered play-count observations: 75 (3 new this run)
- Accumulated probe-history rows: 12916 (22 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Monster Love | metrics_json | `http://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | gameplays_count_with_delimiter | 10103 |
| Monster Love | metrics_json | `http://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | gameplays_count_with_delimiter | 10103 |
| Monster Love | metrics_json | `http://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | gameplays_count_with_delimiter | 10103 |
| Monster Love | metrics_json | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | gameplays_count_with_delimiter | 10103 |
| Monster Love | metrics_json | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | gameplays_count_with_delimiter | 10103 |
| Monster Love | metrics_json | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | gameplays_count_with_delimiter | 10103 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Monster Love | metrics_json | `http://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | 1 |
| Monster Love | metrics_json | `http://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | 1 |
| Monster Love | metrics_json | `http://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | 1 |
| Monster Love | metrics_json | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | 1 |
| Monster Love | metrics_json | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | 1 |
| Monster Love | metrics_json | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | `https://www.kongregate.com/games/esthetix/monster-love/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`