# Archived Count Source Probe

- Generated: 2026-07-03T21:35:23Z
- Target games: 9
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 9
- Endpoint candidates checked: 18
- Candidate observation rows: 18
- CDX status counts: cached=1, fetched=17
- CDX rows found: 4
- Candidates with CDX rows: 4
- Payloads with count-like signals: 4
- Parsed play-count rows: 4
- Deduped recovered play-count observations: 651 (2 new this run)
- Accumulated probe-history rows: 16076 (18 new, 0 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Tanki Online | metrics_json | `http://www.kongregate.com/games/tankionlineuser/tanki-online/metrics.json` | `http://www.kongregate.com:80/games/tankionlineuser/tanki-online/metrics.json` | gameplays_count_with_delimiter | 1343409 |
| Tanki Online | metrics_json | `https://www.kongregate.com/games/tankionlineuser/tanki-online/metrics.json` | `http://www.kongregate.com:80/games/tankionlineuser/tanki-online/metrics.json` | gameplays_count_with_delimiter | 1343409 |
| Straw Hat Samurai: Duels | metrics_json | `http://www.kongregate.com/games/Lutgames/straw-hat-samurai-duels/metrics.json` | `http://www.kongregate.com:80/games/Lutgames/straw-hat-samurai-duels/metrics.json` | gameplays_count_with_delimiter | 510730 |
| Straw Hat Samurai: Duels | metrics_json | `https://www.kongregate.com/games/Lutgames/straw-hat-samurai-duels/metrics.json` | `http://www.kongregate.com:80/games/Lutgames/straw-hat-samurai-duels/metrics.json` | gameplays_count_with_delimiter | 510730 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Tanki Online | metrics_json | `http://www.kongregate.com/games/tankionlineuser/tanki-online/metrics.json` | `http://www.kongregate.com:80/games/tankionlineuser/tanki-online/metrics.json` | 1 |
| Tanki Online | metrics_json | `https://www.kongregate.com/games/tankionlineuser/tanki-online/metrics.json` | `http://www.kongregate.com:80/games/tankionlineuser/tanki-online/metrics.json` | 1 |
| Straw Hat Samurai: Duels | metrics_json | `http://www.kongregate.com/games/Lutgames/straw-hat-samurai-duels/metrics.json` | `http://www.kongregate.com:80/games/Lutgames/straw-hat-samurai-duels/metrics.json` | 1 |
| Straw Hat Samurai: Duels | metrics_json | `https://www.kongregate.com/games/Lutgames/straw-hat-samurai-duels/metrics.json` | `http://www.kongregate.com:80/games/Lutgames/straw-hat-samurai-duels/metrics.json` | 1 |

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`