# Interview Guide

This project demonstrates a synthetic RTO module-level SPC dashboard.

Key talking points:

- Thickness monitoring uses RTR Mean, X-BAR, WIW Stdev, and SIGMA.
- Particle monitoring uses Total, Cluster, and Large Adder thresholds.
- Limits are baseline-only and per stream.
- Fleet charts are visualization-only and do not calculate shared SPC limits.
- Events are persisted to `excursion_events.csv`.
- Local deterministic summaries do not call any hosted service.

The project does not determine cause automatically.
