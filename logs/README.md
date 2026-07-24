# Reports

This directory contains generated snapshots of scrape runs and quality checks. The files remain at this level because the scripts write stable report names here; that keeps refreshes simple and makes report links durable.

Start with these reports:

- `v1_completion_audit_report.*`: release-readiness checks and final evidence buckets for every remaining recovery priority.
- `data_quality_report.*`: coverage, chronology, cache, and count-consistency checks.
- `no_history_evidence_summary_report.*`: evidence behind games that still lack a per-game play-count history.
- `ranked_games_observed_plays_report.*`: direct-listing versus aggregate as-of coverage.
- `game_lifecycle_catalog_report.*`: catalog categories, date evidence, and removal-status summaries.

The remaining report families are grouped by function:

- `*_report.*` with `ranked`, `full_scrape`, `modern_frame`, or `live_`: ranked-list collection and current-page refreshes.
- `*_report.*` with `metrics`, `game_page`, `count_source`, or `developer_game_list`: per-game and alternate-source count recovery.
- `*_audit_report.*`, `*_gap_*`, and `*_evidence_*`: QA, feasibility, and finalization analysis.

For the chronological story of the project, see [progress/README.md](progress/README.md). Git history is the authoritative detailed record for each numbered checkpoint.
