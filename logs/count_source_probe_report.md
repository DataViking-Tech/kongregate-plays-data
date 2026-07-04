# Archived Count Source Probe

- Generated: 2026-07-04T03:12:18Z
- Target games: 32
- Status filter: none
- Games with cached archived pages: 0
- Games direct-probed from catalog URLs: 17
- Endpoint candidates checked: 30
- Candidate observation rows: 32
- CDX status counts: failed=2, fetched=30
- CDX rows found: 130
- Candidates with CDX rows: 10
- Payloads with count-like signals: 6
- Parsed play-count rows: 6
- Deduped recovered play-count observations: 809 (3 new this run)
- Accumulated probe-history rows: 18855 (30 new, 2 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Sword Fight | metrics_json | `http://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | gameplays_count_with_delimiter | 2292002 |
| Sword Fight | metrics_json | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | gameplays_count_with_delimiter | 2292002 |
| Sword Fight | metrics_json | `http://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | gameplays_count_with_delimiter | 1935668 |
| Sword Fight | metrics_json | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | gameplays_count_with_delimiter | 1935668 |
| Royal Squad | metrics_json | `http://www.kongregate.com/games/platon_skedow/royal-squad/metrics.json` | `http://www.kongregate.com/games/platon_skedow/royal-squad/metrics.json` | gameplays_count_with_delimiter | 620055 |
| Royal Squad | metrics_json | `https://www.kongregate.com/games/platon_skedow/royal-squad/metrics.json` | `http://www.kongregate.com/games/platon_skedow/royal-squad/metrics.json` | gameplays_count_with_delimiter | 620055 |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Sword Fight | metrics_json | `http://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | 31 |
| Sword Fight | metrics_json | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | 31 |
| Sword Fight | metrics_json | `http://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | 31 |
| Sword Fight | metrics_json | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | `https://www.kongregate.com/games/tovrick/sword-fight/metrics.json` | 31 |
| Royal Squad | metrics_json | `http://www.kongregate.com/games/platon_skedow/royal-squad/metrics.json` | `http://www.kongregate.com/games/platon_skedow/royal-squad/metrics.json` | 1 |
| Royal Squad | metrics_json | `https://www.kongregate.com/games/platon_skedow/royal-squad/metrics.json` | `http://www.kongregate.com/games/platon_skedow/royal-squad/metrics.json` | 1 |
| Jungle Wars | metrics_json | `http://www.kongregate.com/games/tensquaregames/jungle-wars/metrics.json` | `http://www.kongregate.com/games/tensquaregames/jungle-wars/metrics.json` | 1 |
| Jungle Wars | metrics_json | `https://www.kongregate.com/games/tensquaregames/jungle-wars/metrics.json` | `http://www.kongregate.com/games/tensquaregames/jungle-wars/metrics.json` | 1 |
| The Money Makers | metrics_json | `http://www.kongregate.com/games/AlpagaGames/the-money-makers/metrics.json` | `http://www.kongregate.com/games/AlpagaGames/the-money-makers/metrics.json` | 1 |
| The Money Makers | metrics_json | `https://www.kongregate.com/games/AlpagaGames/the-money-makers/metrics.json` | `http://www.kongregate.com/games/AlpagaGames/the-money-makers/metrics.json` | 1 |

## Retry Note

2 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`