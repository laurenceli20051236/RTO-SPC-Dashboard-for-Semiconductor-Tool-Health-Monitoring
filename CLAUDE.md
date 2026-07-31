# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

This repo has an unusual top level: the real Python project lives entirely inside
`github_project_export/`, not at the repo root. The root only contains a top-level
`README.md` and this `github_project_export/` folder, which is a self-contained
"GitHub upload package" (see `github_project_export/GITHUB_UPLOAD_MANIFEST.md`) meant
to become a repo root on its own when published. **All commands below must be run from
inside `github_project_export/`.**

```
github_project_export/
├── app/                 # Streamlit dashboard (entry point + numbered pages)
├── src/
│   ├── rto_spc/         # The dashboard's Python package (see Architecture below)
│   └── rta_optimizer/   # Separate, dormant subsystem — not wired into the dashboard
├── scripts/             # CLI entry points (data gen, validation, packaging)
├── data/                # Generated CSV outputs (regenerated, not hand-edited)
├── configs/              # YAML config for rta_optimizer's PM deferral engine
├── tests/                # pytest suite, one file per src module (+ some duplicates, see below)
├── docs/                 # Portfolio/methodology docs; some are required by tests
└── notebooks/
```

## Commands

Run from `github_project_export/`:

```bash
# install
pip install -r requirements.txt        # or: pip install -e .

# generate the synthetic CSVs under data/ (deterministic, seed=42)
python scripts/generate_sample_data.py

# run all tests
pytest

# run a single test file / test
pytest tests/test_control_limits.py
pytest tests/test_control_limits.py::test_name_here -v

# validate that data/*.csv match the required schemas
python scripts/validate_data.py

# check release readiness (README/docs claims, disclaimer text, required files)
python scripts/validate_release.py

# launch the dashboard (http://localhost:8501)
streamlit run app/dashboard.py

# build a portable review bundle / a clean GitHub upload zip
python scripts/create_review_bundle.py
python scripts/create_github_export.py
```

There is no linter or CI workflow configured in this repo — `pytest` and
`scripts/validate_release.py` are the correctness gates.

## Architecture: `src/rto_spc`

The dashboard is a small, deterministic, one-directional data pipeline. Nothing in the
UI recalculates SPC status — the app only reads precomputed CSVs.

```
data_generator.py  →  control_limits.py  →  thickness_monitor_rules.py
                                          →  particle_rules.py
                                          →  excursion_scoring.py  →  data/excursion_events.csv
                                                                   →  app/ (chart_helpers.py + pages)
```

- `config.py` — single source of truth for tool/chamber/recipe/metric names, particle
  thresholds, and SPC sigma constants. Grep here first when a metric or threshold name
  looks unfamiliar; other modules import from it rather than hardcoding values.
- `data_generator.py` — synthetic measurement generation, deterministic under
  `RANDOM_SEED = 42`.
- `control_limits.py` — computes baseline-only control limits per stream, where a
  "stream" is always the group `tool_id + chamber_id + recipe_group + metric_name`.
  Two variants exist: simple 3-sigma limits (`apply_baseline_thickness_limits`) and
  I-MR chart limits (`apply_baseline_imr_limits`, gated on
  `MIN_BASELINE_INDIVIDUAL_POINTS`, with optional golden-tool referencing).
- `thickness_monitor_rules.py` / `particle_rules.py` — deterministic rule engines that
  turn measurements + limits into `warning_flag` / `ooc_flag` / `rule_triggered` /
  `severity`. Particle rules also implement repeated-event escalation (3+ warnings in
  the last 10 points of the same stream).
- `spc_rules.py` — the individuals/moving-range (I-MR) fallback rule set, used by
  `chart_helpers.py` for streams too short for the standard baseline limits.
- `excursion_scoring.py` — converts every warning/OOC row into a row of
  `data/excursion_events.csv`; every flagged row in `spc_results.csv` must produce a
  corresponding event.
- `data_loader.py` — the only place that resolves `DATA_DIR` (`github_project_export/data`)
  and reads the three CSVs; keep CSV I/O here rather than scattering `pd.read_csv` calls.
- `schemas.py` / `schema_validation.py` — required-column contracts for the three CSVs,
  checked by `scripts/validate_data.py` and surfaced in the dashboard's validation panel.
- `chart_helpers.py` — all Plotly figure construction for fleet and single-stream views;
  consumes precomputed columns only, never re-derives SPC status.
- `tool_health.py` — synthetic per-tool health score from weighted recent event counts
  (explicitly not a production disposition rule).
- `ai_summary.py` — despite the name, this is a deterministic rule-based summarizer over
  SPC/threshold results, not a hosted AI/LLM call.

### Core invariants (enforced by tests — do not violate silently)

- **Baseline-only limits**: control limits are computed only from rows where
  `phase == "baseline"`; monitoring-phase data is evaluated against those frozen limits
  and must never feed back into them.
- **Per-stream isolation**: SPC/particle calculations never combine data across
  different `tool_id + chamber_id + recipe_group + metric_name` groups.
- **Fleet charts are visualization-only**: multi-tool/chamber overlays must reuse each
  stream's own precomputed limits/flags — never compute a shared "fleet-wide" limit.
- **Every warning/OOC row becomes an event**: `excursion_scoring.py` must produce one
  `excursion_events.csv` row per flagged `spc_results.csv` row.

### `src/rta_optimizer`

A separate "RTO Module Maintenance Cost Optimizer" package (PM deferral engine, cost
model, wafer map, oxide SPC). It is not imported by `app/` or `rto_spc/`, and has no
tests. `configs/pm_deferral_default.yaml` configures its PM deferral thresholds. Treat
it as an independent, currently-dormant subsystem — don't assume it's exercised by the
dashboard or its tests.

## Dashboard (`app/`)

`app/dashboard.py` is the Streamlit entry point (project overview, regenerate-data
button, schema validation panel). `app/pages/` holds five numbered pages that Streamlit
auto-orders in the sidebar, each corresponding to one pipeline stage:

1. `1_Tool_Health_Summary.py` — fleet-wide health scores and event distribution
2. `2_Thickness_Monitor.py` — X-BAR (`thickness_rtr_mean`) / SIGMA (`thickness_wiw_stdev`) charts
3. `3_Particle_Alerts.py` — Total/Cluster/Large adder threshold + escalation charts
4. `4_Excursion_Review.py` — full excursion event table, filters, CSV export
5. `5_Local_Event_Summary.py` — deterministic per-event summary (via `ai_summary.py`)

## Testing conventions

- `tests/` largely mirrors `src/rto_spc/` one-to-one (e.g. `test_control_limits.py`,
  `test_particle_rules.py`).
- A few modules have two independent test files (`test_particle_rules.py` +
  `test_particle_rules_corrected.py`, `test_excursion_scoring.py` +
  `test_excursion_scoring_corrected.py`) using different fixture styles against the same
  module — both must keep passing; don't assume one supersedes the other.
- `test_documentation_required_files.py` and `test_step6_phase1_gate.py` assert that
  specific files under `docs/` (and screenshot placeholders) exist. If you rename or
  remove a doc, update these tests in the same change.
- `test_release_validation.py` exercises `scripts/validate_release.py`, which checks
  the README/docs for the exact synthetic-data disclaimer wording — keep that wording
  consistent if you edit disclaimers.

## Project scope and constraints

This is a **synthetic, portfolio-demo** project, not a production SPC system — this
shapes what changes are appropriate:

- All monitor data, tool IDs, recipes, and limits are synthetic/deterministic
  (seed `42`). Never introduce real fab data, real tool/recipe identifiers, or
  real process limits.
- Scope is intentionally RTO-only: no furnace/FDC/APC modeling, no automated
  root-cause determination, no hosted AI/LLM calls (`ai_summary.py` must stay
  deterministic and rule-based).
- The synthetic-data disclaimer text is checked verbatim by
  `scripts/validate_release.py` / `test_release_validation.py` — if you touch it in one
  place (README, `app/dashboard.py`), keep it consistent everywhere.
