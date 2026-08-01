# Corrected Phase 1 Release Checklist

- [ ] `python scripts/generate_sample_data.py` runs successfully.
- [ ] `pytest` passes.
- [ ] `streamlit run app/dashboard.py` launches.
- [ ] Required CSV files exist and are non-empty.
- [ ] Required thickness and particle metrics exist.
- [ ] Thickness page shows RTR Mean, X-BAR, WIW Stdev, and SIGMA.
- [ ] Particle page shows Total, Cluster, and Large Adder threshold alerts.
- [ ] Fleet charts do not calculate shared SPC limits.
- [ ] All warning/OOC rows persist to `excursion_events.csv`.
- [ ] README contains the exact synthetic-data disclaimer.
- [ ] No real-data claim appears.
- [ ] No automatic-cause claim appears.
- [ ] No hosted-service key is required.
