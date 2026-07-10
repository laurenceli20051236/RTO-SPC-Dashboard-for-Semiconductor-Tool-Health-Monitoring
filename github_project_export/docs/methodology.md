# Methodology

This project is an RTO-only synthetic Phase 1 dashboard.

Thickness monitoring uses four module-level metrics:

- `thickness_rtr_mean`
- `thickness_xbar`
- `thickness_wiw_stdev`
- `thickness_sigma`

Thickness limits are calculated from `phase == "baseline"` rows only and are grouped by `tool_id`, `chamber_id`, `recipe_group`, and `metric_name`.

Particle monitoring uses three adder metrics:

- `particle_total_adder`
- `particle_cluster_adder`
- `particle_large_adder`

Particle alerts use fixed synthetic Warning/High thresholds plus repeated-event escalation. Count charts are not used as the primary Phase 1 alert method.

All warning and OOC rows are persisted to `data/excursion_events.csv`.

The dashboard does not determine cause automatically and does not replace engineering review.
