# Data Dictionary

## data/monitor_measurements.csv

Required columns:

- `timestamp`
- `phase`
- `tool_id`
- `chamber_id`
- `recipe_group`
- `monitor_type`
- `metric_name`
- `value`
- `unit`
- `lot_id_hash`
- `monitor_wafer_id_hash`
- `measurement_id`
- `sequence_id`

Required metrics:

- `thickness_rtr_mean`
- `thickness_xbar`
- `thickness_wiw_stdev`
- `thickness_sigma`
- `particle_total_adder`
- `particle_cluster_adder`
- `particle_large_adder`

## data/spc_results.csv

Adds baseline-only limit and rule-result columns:

- `baseline_mean`
- `baseline_sigma`
- `ucl`
- `cl`
- `lcl`
- `warning_flag`
- `ooc_flag`
- `rule_triggered`
- `severity`

## data/excursion_events.csv

Stores one event row for every warning or OOC row from `spc_results.csv`.

Required event fields include `event_id`, `timestamp`, `phase`, stream identity columns, value/limit columns, `rule_triggered`, `severity`, `suggested_review_area`, `status`, and `comment`.
