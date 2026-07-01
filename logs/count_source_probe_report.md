# Archived Count Source Probe

- Generated: 2026-07-01T22:19:07Z
- Target games: 9
- Status filter: transient_failures_remaining
- Games with cached archived pages: 3
- Games direct-probed from catalog URLs: 6
- Endpoint candidates checked: 88
- Candidate observation rows: 89
- CDX status counts: cached=27, fetched=62
- CDX rows found: 23
- Candidates with CDX rows: 5
- Payloads with count-like signals: 2
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 1 (0 new this run)
- Accumulated probe-history rows: 6550 (88 new, 1 refreshed)

## Count Signals

| Game | Source | Endpoint | Sample | Signal | Plays |
| --- | --- | --- | --- | --- | --- |
| Penguin Heroes | holodeck | `http://cdn4.kongregate.com/javascripts/holodeck_javascripts.js?1324512375` | `http://cdn4.kongregate.com/javascripts/holodeck_javascripts.js?1324512375` | term_only | n/a |
| Penguin Heroes | holodeck | `http://cdn4.kongregate.com/javascripts/holodeck_javascripts.js?1324512375` | `http://cdn4.kongregate.com/javascripts/holodeck_javascripts.js?1324512375` | term_only | n/a |

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Penguin Heroes | holodeck | `http://cdn4.kongregate.com/javascripts/holodeck_javascripts.js?1324512375` | `http://cdn4.kongregate.com/javascripts/holodeck_javascripts.js?1324512375` | 10 |
| Penguin Heroes | holodeck | `http://cdn4.kongregate.com/javascripts/holodeck_javascripts.js?1324512375` | `http://cdn4.kongregate.com/javascripts/holodeck_javascripts.js?1324512375` | 10 |
| Bubble Shooter Exclusive | holodeck | `http://www.kongregate.com/games/fighter106/bubble-shooter-exclusive/holodeck` | `http://www.kongregate.com/games/fighter106/bubble-shooter-exclusive/holodeck` | 1 |
| Bubble Shooter Exclusive | holodeck | `https://www.kongregate.com/games/fighter106/bubble-shooter-exclusive/holodeck` | `http://www.kongregate.com/games/fighter106/bubble-shooter-exclusive/holodeck` | 1 |
| Electro City | recommended_games | `http://www.kongregate.com/recommended_games?game_id=119414&gamepage_pod=true` | `http://www.kongregate.com/recommended_games?game_id=119414&gamepage_pod=true` | 1 |

## Interpretation

The only count-like terms sampled here were non-public placeholders or guest/user counters, not numeric game play totals. No endpoint payload in this run produced a trusted play-count observation.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`