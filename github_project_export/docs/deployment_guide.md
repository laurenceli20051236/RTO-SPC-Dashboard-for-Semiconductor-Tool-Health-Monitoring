# Deployment Guide

## Local Review

```bash
python -m pip install -r requirements.txt
python scripts/generate_sample_data.py
python scripts/validate_data.py
streamlit run app/dashboard.py
```

Open the app at the local URL printed by Streamlit.

Local URLs such as `127.0.0.1:8501` and `localhost:8501` only work on the machine running Streamlit. For ChatGPT or remote reviewer debugging, generate the portable review bundle instead:

```bash
python scripts/create_review_bundle.py
```

The bundle is written to `reports/chatgpt_review_bundle.zip`.

## Streamlit Cloud

Use these settings:

| Setting | Value |
|---|---|
| Repository | `rto-spc-dashboard` |
| Branch | main portfolio branch |
| Main file path | `app/dashboard.py` |
| Python version | 3.11 or newer |
| Secrets | none required |

Before deployment, commit generated sample CSV files or configure the app reviewer to run:

```bash
python scripts/generate_sample_data.py
```

No hosted-service key, database, or production data source is required.

## CI Gate

GitHub Actions runs:

```bash
python -m pip install -r requirements.txt
python scripts/generate_sample_data.py
python scripts/validate_data.py
pytest
```

This verifies that synthetic data generation, schema validation, and tests remain healthy.
