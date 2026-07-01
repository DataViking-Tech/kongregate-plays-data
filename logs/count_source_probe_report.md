# Archived Count Source Probe

- Generated: 2026-07-01T05:11:55Z
- Target games: 7
- Games with cached archived pages: 7
- Endpoint candidates checked: 70
- CDX status counts: cached=24, failed=27, fetched=19
- CDX rows found: 24
- Candidates with CDX rows: 8
- Payloads with count-like signals: 4
- Parsed play-count rows: 0

## Count Signals

| Game | Source | Endpoint | Signal | Plays |
| --- | --- | --- | --- | ---: |
| Crazy Zombie v2.0 Crossing Hero | comments | `http://www.kongregate.com/games/game4joy/crazy-zombie-v2-0-crossing-hero/comments/` | gameplays_count | 0 |
| Crazy Zombie v2.0 Crossing Hero | comments | `https://www.kongregate.com/games/game4joy/crazy-zombie-v2-0-crossing-hero/comments/` | gameplays_count | 0 |
| Mike Shadow: I Paid For It! (Mochi Premiums) | comments | `http://www.kongregate.com/games/Allkiko1/mike-shadow-i-paid-for-it-mochi-premiums/comments/` | gameplays_count | 0 |
| Mike Shadow: I Paid For It! (Mochi Premiums) | comments | `https://www.kongregate.com/games/Allkiko1/mike-shadow-i-paid-for-it-mochi-premiums/comments/` | gameplays_count | 0 |

## Archived Endpoint Hits

| Game | Source | Endpoint | CDX rows |
| --- | --- | --- | ---: |
| Crazy Zombie v2.0 Crossing Hero | comments | `http://www.kongregate.com/games/game4joy/crazy-zombie-v2-0-crossing-hero/comments/` | 4 |
| Crazy Zombie v2.0 Crossing Hero | comments | `https://www.kongregate.com/games/game4joy/crazy-zombie-v2-0-crossing-hero/comments/` | 4 |
| Mike Shadow: I Paid For It! (Mochi Premiums) | comments | `http://www.kongregate.com/games/Allkiko1/mike-shadow-i-paid-for-it-mochi-premiums/comments/` | 2 |
| Mike Shadow: I Paid For It! (Mochi Premiums) | comments | `https://www.kongregate.com/games/Allkiko1/mike-shadow-i-paid-for-it-mochi-premiums/comments/` | 2 |
| Mike Shadow: I Paid For It! (Mochi Premiums) | holodeck | `http://www.kongregate.com/games/Allkiko1/mike-shadow-i-paid-for-it-mochi-premiums/holodeck` | 5 |
| Mike Shadow: I Paid For It! (Mochi Premiums) | holodeck | `https://www.kongregate.com/games/Allkiko1/mike-shadow-i-paid-for-it-mochi-premiums/holodeck` | 5 |
| Bubble Shooter Exclusive | comments | `https://www.kongregate.com/games/fighter106/bubble-shooter-exclusive/comments/` | 1 |
| Crazy Zombie v2.0 Crossing Hero | holodeck | `https://www.kongregate.com/games/game4joy/crazy-zombie-v2-0-crossing-hero/holodeck` | 1 |

## Interpretation

The only count-like terms sampled here were non-public placeholders or guest/user counters, not numeric game play totals. No endpoint payload in this run produced a trusted play-count observation.

## Retry Note

27 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `logs/count_source_probe_report.json`