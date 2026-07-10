# GitHub Upload Manifest

Upload the contents of this folder as the GitHub repository root.

## Included

* .github
* .gitignore
* README.md
* app
* configs
* data
* docs
* notebooks
* pyproject.toml
* requirements.txt
* scripts
* src
* tests

## Not Included

* `.git/` local repository metadata
* `.agents/` local Codex metadata
* `.pytest_cache/`, `__pycache__/`, and Python bytecode
* `tmp/` local logs
* generated review/export zips under `reports/`

## Quick Start

```bash
python -m pip install -r requirements.txt
python scripts/generate_sample_data.py
pytest
streamlit run app/dashboard.py
```

The included CSV files under `data/` are synthetic demo data only.
