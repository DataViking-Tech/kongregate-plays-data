# High-Value No-CDX Targeted Probe

- Generated: 2026-07-01T04:48:36Z
- Target games: 7
- Archived game-page CDX rows checked: 372
- Archived game-page jobs attempted: 94
- Trusted game-page play-count rows recovered: 0
- Expanded metrics-route games checked: 7
- Expanded metrics-route CDX rows found: 0
- Expanded metrics-route metrics rows recovered: 0
- Per-game history rows after probe: 7932
- Canonical games with per-game history after probe: 2667

## Target Results

| Game | Tier | Page CDX rows | Page jobs | Trusted page rows | Expanded metrics CDX rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| RPgTest | 1 | 8 | 2 | 0 | 0 |
| Mining Truck | 1 | 10 | 2 | 0 | 0 |
| Swimwear Store | 1 | 5 | 1 | 0 | 0 |
| Crazy Zombie v2.0 Crossing Hero | 1 | 155 | 31 | 0 | 0 |
| Tap Tap Infinity | 1 | 65 | 13 | 0 | 0 |
| Mike Shadow: I Paid For It! (Mochi Premiums) | 1 | 117 | 39 | 0 | 0 |
| Bubble Shooter Exclusive | 2 | 12 | 6 | 0 | 0 |

## Interpretation

The seven high-value no-CDX games were dry across both conservative archived game-page parsing and expanded archived `metrics.json` route probing. Ranked-list rows still exist for these games, but the 2014+ list layouts and the archived game pages checked here do not expose trusted static play-count text. Future recovery for these names likely needs a different source shape, not another broad replay of the same page parser.

Representative cached page inspection for Crazy Zombie v2.0 Crossing Hero, Tap Tap Infinity, Bubble Shooter Exclusive, and Mike Shadow found empty `gameplays_count` placeholder spans plus guest/user `gameplays_count: 0` values, not embedded public game-play totals. That supports treating the dry result as source absence rather than a simple parser miss.
