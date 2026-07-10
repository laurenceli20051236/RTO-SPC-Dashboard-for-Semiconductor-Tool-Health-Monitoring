# RTO SPC Dashboard

This is an RTO-only synthetic dashboard.

This project uses fully synthetic and anonymized semiconductor monitor data for public portfolio demonstration only. It does not contain real tool identifiers, real recipe names, real product information, real wafer records, real lot records, real process limits, real SPC limits, or any confidential manufacturing information.

## Scope

The dashboard validates a corrected Phase 1 RTO monitor workflow:

- Thickness Phase 1 uses RTR Mean, X-BAR, WIW Stdev, and SIGMA.
- Particle Phase 1 uses Total Adder, Cluster Adder, and Large Adder threshold + repeated-event alerts.
- Limits are calculated from baseline data only.
- Limits are calculated per tool/chamber/recipe/metric stream.
- Fleet charts are visualization-only and do not calculate shared SPC limits.
- All alerts are persisted to excursion_events.csv.

No process-index layer, particle control-chart overlay, hosted AI service, automated diagnosis, FDC, APC, maintenance-correlation layer, or production-data ingestion is included.

## Dashboard Pages

- Tool Health Summary
- RTO Thickness Monitor
- Particle Alerts
- Excursion Review
- Local Event Summary

## Data Outputs

Running the sample-data generator creates:

- `data/monitor_measurements.csv`
- `data/spc_results.csv`
- `data/excursion_events.csv`

`monitor_measurements.csv` contains baseline and monitoring rows for four synthetic RTO tools, two chambers, two recipe groups, four thickness metrics, and three particle metrics.

`spc_results.csv` stores precomputed baseline-only limits, warning flags, OOC flags, rule IDs, and severity.

`excursion_events.csv` stores one event row for every warning or OOC row in `spc_results.csv`.

## Thickness Logic

The primary RTO thickness monitor metrics are:

- `thickness_rtr_mean`
- `thickness_xbar`
- `thickness_wiw_stdev`
- `thickness_sigma`

Mean-style metrics trigger `THICKNESS_BEYOND_CONTROL_LIMIT` outside UCL/LCL and `THICKNESS_WARNING_ZONE` beyond +/-2 baseline sigma but within limits.

Variation metrics trigger `THICKNESS_VARIATION_HIGH` above UCL. Lower limits for nonnegative variation metrics may be clipped at zero.

## Particle Logic

The primary particle metrics are:

- `particle_total_adder`
- `particle_cluster_adder`
- `particle_large_adder`

Synthetic thresholds:

| Metric | Warning | High |
| --- | ---: | ---: |
| `particle_total_adder` | 10 | 20 |
| `particle_cluster_adder` | 3 | 6 |
| `particle_large_adder` | 1 | 3 |

Particle alerts use `PARTICLE_THRESHOLD_WARNING`, `PARTICLE_THRESHOLD_HIGH`, and `PARTICLE_REPEATED_EVENT_ESCALATION`.

## Run Locally

```bash
python scripts/generate_sample_data.py
pytest
streamlit run app/dashboard.py
```

Open the dashboard at:

```text
http://127.0.0.1:8501/
```

## Review Package

For ChatGPT or remote review, build a portable package:

```bash
python scripts/create_review_bundle.py
```

The local Streamlit URL only works on the machine running the app.

## GitHub Export

To create a clean GitHub upload package:

```bash
python scripts/create_github_export.py
```

This writes `reports/rto_spc_dashboard_github_export.zip`. Upload the contents of the zip as the repository root.

The export includes the synthetic CSVs under `data/` so the dashboard opens with demo data immediately.

## Safety Notes

This dashboard does not determine cause automatically.
It does not provide production disposition.
It is a deterministic synthetic QA/demo project for RTO monitor SPC review.
