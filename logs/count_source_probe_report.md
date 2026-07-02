# Archived Count Source Probe

- Generated: 2026-07-02T11:57:54Z
- Target games: 4
- Status filter: transient_failures_remaining
- Games with cached archived pages: 4
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 10
- Candidate observation rows: 10
- CDX status counts: cached=8, failed=1, fetched=1
- CDX rows found: 33
- Candidates with CDX rows: 9
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 6 (0 new this run)
- Accumulated probe-history rows: 9419 (6 new, 4 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Surrounded | game_path_prefix | `http://www.kongregate.com/games/JasonNumberXIII/surrounded` | `https://www.kongregate.com/games/JasonNumberXIII/surrounded` | 7 |
| Surrounded | game_path_prefix | `http://www.kongregate.com/games/JasonNumberXIII/surrounded` | `https://www.kongregate.com/games/JasonNumberXIII/surrounded` | 7 |
| Surrounded | game_path_prefix | `https://www.kongregate.com/games/JasonNumberXIII/surrounded` | `https://www.kongregate.com/games/JasonNumberXIII/surrounded` | 7 |
| Surrounded | game_path_prefix | `https://www.kongregate.com/games/JasonNumberXIII/surrounded` | `https://www.kongregate.com/games/JasonNumberXIII/surrounded` | 7 |
| Mini Jumper | game_path_prefix | `http://www.kongregate.com/games/mafagames/mini-jumper` | `http://www.kongregate.com:80/games/mafagames/mini-jumper` | 1 |
| Mini Jumper | game_path_prefix | `https://www.kongregate.com/games/mafagames/mini-jumper` | `http://www.kongregate.com:80/games/mafagames/mini-jumper` | 1 |
| Missiles Again | game_path_prefix | `http://www.kongregate.com/games/mafagames/missiles-again` | `http://www.kongregate.com:80/games/mafagames/missiles-again` | 1 |
| Missiles Again | game_path_prefix | `https://www.kongregate.com/games/mafagames/missiles-again` | `http://www.kongregate.com:80/games/mafagames/missiles-again` | 1 |
| Run Bird Run Online | game_path_prefix | `https://www.kongregate.com/games/mafagames/run-bird-run-online` | `http://www.kongregate.com:80/games/mafagames/run-bird-run-online` | 1 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Retry Note

1 CDX lookups failed during this run, so dry endpoints with failed status should be retried later before being treated as durable absences.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`