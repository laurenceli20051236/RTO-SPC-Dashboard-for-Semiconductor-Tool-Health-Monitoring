# Methodology Summary

Phase 1 is limited to deterministic RTO monitor SPC and threshold alerting.

Thickness Phase 1 uses RTR Mean, X-BAR, WIW Stdev, and SIGMA. Limits are baseline-only and per stream.

Particle Phase 1 uses Total Adder, Cluster Adder, and Large Adder thresholds with repeated-event escalation.

Fleet charts are visualization-only. They show multiple tools and chambers using precomputed limits and flags; they do not calculate shared SPC limits.

`excursion_events.csv` is the event persistence layer for every warning and OOC row.
