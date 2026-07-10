# Architecture Overview

```mermaid
flowchart LR
    A["generate_monitor_measurements"] --> B["baseline-only limits"]
    B --> C["thickness rules"]
    C --> D["particle threshold rules"]
    D --> E["excursion_events.csv"]
    E --> F["Streamlit Phase 1 pages"]
```

The pipeline is intentionally small:

- `data_generator.py` creates synthetic RTO monitor measurements.
- `control_limits.py` calculates baseline-only per-stream limits for thickness rows.
- `thickness_monitor_rules.py` applies Phase 1 thickness rules.
- `particle_rules.py` applies threshold and repeated-event particle rules.
- `excursion_scoring.py` persists every warning/OOC row as an event.
- `chart_helpers.py` renders fleet and selected-stream visualizations from precomputed results.

The dashboard does not recalculate OOC status in the UI.
