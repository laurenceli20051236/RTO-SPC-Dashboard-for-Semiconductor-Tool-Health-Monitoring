# ChatGPT Review Package

The local Streamlit URL is not externally reachable. Use:

```bash
python scripts/create_review_bundle.py
```

The generated ZIP includes the Phase 1 dashboard code, docs, screenshots, and synthetic CSV outputs needed for review.

Recommended review order:

1. `README.md`
2. `docs/methodology.md`
3. `app/dashboard.py`
4. `app/pages/2_Thickness_Monitor.py`
5. `app/pages/3_Particle_Alerts.py`
6. `data/excursion_events.csv`

Review scope is corrected Phase 1 only.
