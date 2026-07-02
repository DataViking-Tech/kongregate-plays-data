# Archived Count Source Probe

- Generated: 2026-07-02T00:36:17Z
- Target games: 5
- Status filter: archived_endpoint_hit_no_count
- Games with cached archived pages: 5
- Games direct-probed from catalog URLs: 0
- Endpoint candidates checked: 10
- Candidate observation rows: 16
- CDX status counts: cached=16
- CDX rows found: 72
- Candidates with CDX rows: 16
- Payloads with count-like signals: 0
- Parsed play-count rows: 0
- Deduped recovered play-count observations: 1 (0 new this run)
- Accumulated probe-history rows: 7856 (0 new, 16 refreshed)

## Archived Endpoint Hits

| Game | Source | Endpoint | Sample | CDX rows |
| --- | --- | --- | --- | ---: |
| Make Me 10 | game_path_prefix | `http://www.kongregate.com/games/LinhVo1611/make-me-10` | `http://www.kongregate.com:80/games/LinhVo1611/make-me-10` | 8 |
| Make Me 10 | game_path_prefix | `http://www.kongregate.com/games/LinhVo1611/make-me-10` | `http://www.kongregate.com:80/games/LinhVo1611/make-me-10` | 8 |
| Make Me 10 | game_path_prefix | `http://www.kongregate.com/games/LinhVo1611/make-me-10` | `http://www.kongregate.com:80/games/LinhVo1611/make-me-10` | 8 |
| Make Me 10 | game_path_prefix | `http://www.kongregate.com/games/LinhVo1611/make-me-10` | `http://www.kongregate.com:80/games/LinhVo1611/make-me-10` | 8 |
| Make Me 10 | game_path_prefix | `https://www.kongregate.com/games/LinhVo1611/make-me-10` | `http://www.kongregate.com:80/games/LinhVo1611/make-me-10` | 8 |
| Make Me 10 | game_path_prefix | `https://www.kongregate.com/games/LinhVo1611/make-me-10` | `http://www.kongregate.com:80/games/LinhVo1611/make-me-10` | 8 |
| Make Me 10 | game_path_prefix | `https://www.kongregate.com/games/LinhVo1611/make-me-10` | `http://www.kongregate.com:80/games/LinhVo1611/make-me-10` | 8 |
| Make Me 10 | game_path_prefix | `https://www.kongregate.com/games/LinhVo1611/make-me-10` | `http://www.kongregate.com:80/games/LinhVo1611/make-me-10` | 8 |
| Key to Success | game_path_prefix | `http://www.kongregate.com/games/SamuelVenable/key-to-success` | `http://www.kongregate.com:80/games/SamuelVenable/key-to-success` | 1 |
| Key to Success | game_path_prefix | `https://www.kongregate.com/games/SamuelVenable/key-to-success` | `http://www.kongregate.com:80/games/SamuelVenable/key-to-success` | 1 |
| Missiles Again | game_path_prefix | `http://www.kongregate.com/games/mafagames/missiles-again` | `http://www.kongregate.com:80/games/mafagames/missiles-again` | 1 |
| Missiles Again | game_path_prefix | `https://www.kongregate.com/games/mafagames/missiles-again` | `http://www.kongregate.com:80/games/mafagames/missiles-again` | 1 |
| Run Bird Run Online | game_path_prefix | `http://www.kongregate.com/games/mafagames/run-bird-run-online` | `http://www.kongregate.com:80/games/mafagames/run-bird-run-online` | 1 |
| Run Bird Run Online | game_path_prefix | `https://www.kongregate.com/games/mafagames/run-bird-run-online` | `http://www.kongregate.com:80/games/mafagames/run-bird-run-online` | 1 |
| The Space Commando | game_path_prefix | `http://www.kongregate.com/games/Eternal_Vanguard/the-space-commando` | `http://www.kongregate.com:80/games/Eternal_Vanguard/the-space-commando` | 1 |
| The Space Commando | game_path_prefix | `https://www.kongregate.com/games/Eternal_Vanguard/the-space-commando` | `http://www.kongregate.com:80/games/Eternal_Vanguard/the-space-commando` | 1 |

## Interpretation

No sampled alternate endpoint exposed a parseable play-count field in this run. This does not prove the source is absent everywhere; it narrows the next search toward either broader prefix CDX probes, archived JavaScript behavior, or external list pages rather than the already-tested game-page placeholders.

## Output Files

- `data/processed/count_source_probe_candidates.csv`
- `data/processed/count_source_probe_history.csv`
- `data/processed/count_source_play_counts.csv`
- `logs/count_source_probe_report.json`