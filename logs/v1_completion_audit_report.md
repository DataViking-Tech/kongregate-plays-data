# Kongregate V1 Completion Audit

- Generated at: 2026-07-05T05:44:14Z
- Recommendation: `ready_to_call_kongregate_wayback_v1_after_public_note`
- Aggregate as-of coverage: 44906 / 49982 (89.84%)
- Remaining ranked rows without aggregate as-of count: 5076
- Catalog play-history coverage: 2687 / 2998 (89.63%)
- Continuing the old five-game cadence would require about 359 more slices.

## V1 Checks

- PASS: ranked_months_without_aggregate_asof_play_counts_is_zero
- PASS: play_count_decreases_is_zero
- PASS: no_history_unresolved_failed_endpoint_total_is_zero
- PASS: all_priority_rows_have_v1_bucket

## Finalization Buckets

- earlier_history_exact_metrics_only_before_missing_window: 3
- earlier_history_exact_metrics_outside_missing_window: 1
- earlier_history_exact_metrics_overlap_sampled_no_count_signal: 1
- earlier_history_exact_metrics_start_after_gap: 297
- earlier_history_no_exact_metrics_archives: 1437
- no_count_dynamic_placeholder_endpoint_archives_no_count: 91
- no_count_dynamic_placeholder_no_count_source: 44
- no_count_no_page_cdx: 106
- outside_mini_catalog_scope_no_count: 2

## Top Remaining Examples

- #1 Supermechs (274 rows, best rank 2): earlier_history_exact_metrics_start_after_gap
- #2 Bloons Monkey City (530 rows, best rank 4): earlier_history_exact_metrics_start_after_gap
- #3 Crusaders of the Lost Idols (70 rows, best rank 1): earlier_history_exact_metrics_start_after_gap
- #4 Mu Complex : Episode One (20 rows, best rank 1): earlier_history_exact_metrics_start_after_gap
- #5 There is no game (15 rows, best rank 1): earlier_history_exact_metrics_start_after_gap
- #6 Cosmos Quest (19 rows, best rank 1): earlier_history_exact_metrics_start_after_gap
- #7 The Enchanted Cave 2 (39 rows, best rank 1): earlier_history_exact_metrics_start_after_gap
- #8 KingsRoad (27 rows, best rank 4): earlier_history_exact_metrics_start_after_gap
- #9 Blockade3D (24 rows, best rank 3): earlier_history_exact_metrics_start_after_gap
- #10 Superfighters (69 rows, best rank 10): earlier_history_exact_metrics_start_after_gap
- #11 Swarm Simulator (43 rows, best rank 1): earlier_history_exact_metrics_start_after_gap
- #12 N Step Steve: Part 1 (29 rows, best rank 4): earlier_history_no_exact_metrics_archives
- #13 Trimps (24 rows, best rank 3): earlier_history_exact_metrics_start_after_gap
- #14 Sports Heads: Football Championship (14 rows, best rank 3): earlier_history_exact_metrics_start_after_gap
- #15 Realm Grinder (19 rows, best rank 4): earlier_history_exact_metrics_start_after_gap
- #16 Medieval Chronicles 8 (Part 2) (13 rows, best rank 5): earlier_history_exact_metrics_start_after_gap
- #17 Fleeing the Complex (270 rows, best rank 10): earlier_history_exact_metrics_start_after_gap
- #18 Medieval Chronicles 4 (5 rows, best rank 1): earlier_history_exact_metrics_start_after_gap
- #19 Medieval Cop 8 -DeathWish- (Part 3) (12 rows, best rank 3): earlier_history_exact_metrics_start_after_gap
- #20 Unpuzzle 2 (7 rows, best rank 1): earlier_history_exact_metrics_start_after_gap
- #21 Medieval Cop 9 -Song & Silence- (Part 1) (12 rows, best rank 4): earlier_history_exact_metrics_start_after_gap
- #22 The Very Organized Thief (44 rows, best rank 5): earlier_history_exact_metrics_start_after_gap
- #23 Trader of Stories - Chapter 3 (18 rows, best rank 5): earlier_history_no_exact_metrics_archives
- #24 Super Hot (48 rows, best rank 7): earlier_history_exact_metrics_start_after_gap
- #25 Evo Explores (16 rows, best rank 4): earlier_history_exact_metrics_start_after_gap

## Outputs

- `data/processed/v1_completion_audit.csv`
- `logs/v1_completion_audit_report.json`
