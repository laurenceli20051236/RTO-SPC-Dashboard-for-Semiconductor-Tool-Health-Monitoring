# Hiring Manager Quick Start

## Two-Minute Review

1. Open the README and inspect the fleet snapshot, capability table, and architecture diagram.
2. Review the Tool Health page to see fleet prioritization.
3. Review the Thickness page for RTR Mean, X-BAR, WIW Stdev, and SIGMA chamber overlays.
4. Review the Particle page for threshold and repeated-event handling.
5. Review Excursion Review for event traceability and export.

## Run Locally

```bash
python -m pip install -r requirements-dev.txt
python scripts/generate_sample_data.py
python scripts/validate_data.py
pytest
python scripts/validate_release.py
streamlit run app/dashboard.py
```

Open `http://127.0.0.1:8501/` on the same machine.

## What To Evaluate

- Domain-to-code translation
- Baseline integrity and SPC boundary control
- Fleet visualization without shared-limit misuse
- Reproducible data and event pipeline design
- Testing, CI, documentation, and deployment readiness

This is an RTO-only synthetic dashboard and does not contain production data.
