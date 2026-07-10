from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rto_spc.data_loader import DATA_DIR, load_excursion_events
from rto_spc.data_pipeline import generate_all_sample_data
from rto_spc.schema_validation import validate_all_data_files, validation_passed
from rto_spc.config import RANDOM_SEED

DISCLAIMER = (
    "This project uses fully synthetic and anonymized semiconductor monitor data "
    "for public portfolio demonstration only. It does not contain real tool "
    "identifiers, real recipe names, real product information, real wafer records, "
    "real lot records, real process limits, real SPC limits, or any confidential "
    "manufacturing information."
)

st.set_page_config(page_title="RTO SPC Dashboard", layout="wide")

st.title("RTO SPC Dashboard for Semiconductor Tool Health Monitoring")
st.write("Corrected Phase 1 validation dashboard for synthetic RTO module-level thickness and particle monitoring.")
st.info(DISCLAIMER)

st.subheader("Project Overview")
st.write(
    "This dashboard demonstrates a local semiconductor manufacturing analytics workflow: synthetic monitor data generation, "
    "baseline-only SPC calculations, threshold alerts, repeated-event escalation, and excursion event persistence."
)

phase_summary = pd.DataFrame(
    [
        {"Phase": "Phase 1", "Scope": "thickness_rtr_mean / thickness_xbar / thickness_wiw_stdev / thickness_sigma + particle threshold alerts", "Purpose": "Corrected core deterministic SPC MVP"},
    ]
)
st.dataframe(phase_summary, use_container_width=True, hide_index=True)

st.subheader("Portfolio Demo Controls")
left, middle, right = st.columns(3)
with left:
    if st.button("Regenerate sample data", type="primary"):
        outputs = generate_all_sample_data(output_dir=DATA_DIR, seed=RANDOM_SEED)
        st.success(f"Regenerated {len(outputs)} CSV files.")
with middle:
    validation_results = validate_all_data_files(DATA_DIR)
    if validation_passed(validation_results):
        st.success("Data schema validation passed.")
    else:
        st.error("Data schema validation failed.")
with right:
    events = load_excursion_events()
    if events.empty:
        st.metric("Excursion events", 0)
    else:
        high_count = int((events["severity"] == "High").sum())
        st.metric("Excursion events", len(events), delta=f"{high_count} high")

with st.expander("Schema validation details"):
    validation_table = pd.DataFrame(
        [
            {
                "file": result.filename,
                "valid": result.valid,
                "rows": result.row_count,
                "errors": "; ".join(result.errors),
            }
            for result in validation_results
        ]
    )
    st.dataframe(validation_table, use_container_width=True, hide_index=True)

st.subheader("Methodology Summary")
method_left, method_right = st.columns(2)
with method_left:
    st.write("Thickness Phase 1 uses RTR Mean, X-BAR, WIW Stdev, and SIGMA with baseline-only per-stream limits.")
    st.write("Particle Phase 1 uses Total Adder, Cluster Adder, and Large Adder thresholds plus repeated-event alerts.")
with method_right:
    st.write("Fleet charts are visualization-only and use precomputed per-stream limits and event flags.")
    st.write("All warning and OOC rows are persisted to `data/excursion_events.csv`.")

st.subheader("Navigation Guide")
st.write(
    "Use the sidebar to open Tool Health Summary, RTO Thickness Monitor, Particle Alerts, Excursion Review, Local Event Summary, "
    "and validate the corrected Phase 1 workflow."
)

st.subheader("Recommended Demo Path")
st.write("1. Tool Health Summary")
st.write("2. RTO Thickness Monitor")
st.write("3. Particle Alerts")
st.write("4. Excursion Review")
st.write("5. Local Event Summary")

st.subheader("External Review")
st.write(
    "A local Streamlit URL such as `127.0.0.1:8501` only works on this machine. "
    "For ChatGPT or remote debugging review, generate a portable review package with "
    "`python scripts/create_review_bundle.py` and share the ZIP."
)

st.subheader("What This Dashboard Does Not Claim")
st.write("It does not use semiconductor manufacturing production data, determine cause automatically, or replace engineering review.")
