from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rto_spc.chart_helpers import plot_fleet_tool_health_bar, plot_severity_distribution
from rto_spc.config import PARTICLE_METRICS, RANDOM_SEED, THICKNESS_METRICS
from rto_spc.data_loader import DATA_DIR, load_excursion_events, load_spc_results
from rto_spc.data_pipeline import generate_all_sample_data
from rto_spc.schema_validation import validate_all_data_files, validation_passed
from rto_spc.tool_health import TOOL_HEALTH_LABEL, calculate_tool_health

DISCLAIMER = (
    "This project uses fully synthetic and anonymized semiconductor monitor data "
    "for public portfolio demonstration only. It does not contain real tool "
    "identifiers, real recipe names, real product information, real wafer records, "
    "real lot records, real process limits, real SPC limits, or any confidential "
    "manufacturing information."
)

st.set_page_config(page_title="RTO SPC Dashboard", layout="wide")

st.title("RTO Fleet SPC Dashboard")
st.caption("Synthetic semiconductor equipment monitoring portfolio project")
st.info(DISCLAIMER)

events = load_excursion_events()
spc_results = load_spc_results()
health = calculate_tool_health(events)

st.subheader("Fleet Snapshot")
metric_columns = st.columns(4)
with metric_columns[0]:
    st.metric("RTO tools", int(spc_results["tool_id"].nunique()) if not spc_results.empty else 0)
with metric_columns[1]:
    chamber_streams = spc_results[["tool_id", "chamber_id"]].drop_duplicates().shape[0] if not spc_results.empty else 0
    st.metric("Chamber streams", chamber_streams)
with metric_columns[2]:
    st.metric("Monitor metrics", len(THICKNESS_METRICS) + len(PARTICLE_METRICS))
with metric_columns[3]:
    high_count = int((events["severity"] == "High").sum()) if not events.empty else 0
    st.metric("Excursion events", len(events), delta=f"{high_count} high")

health_column, severity_column = st.columns([2, 1])
with health_column:
    st.plotly_chart(plot_fleet_tool_health_bar(health), use_container_width=True)
with severity_column:
    st.plotly_chart(plot_severity_distribution(events), use_container_width=True)
st.caption(TOOL_HEALTH_LABEL)

st.subheader("Engineering Scope")
st.write(
    "RTO thickness monitoring uses RTR Mean, X-BAR, WIW Stdev, and SIGMA with baseline-only per-stream limits. "
    "Particle monitoring uses Total, Cluster, and Large Adder thresholds plus repeated-event escalation."
)
st.write(
    "Control limits stay separate by tool, chamber, recipe, and metric. Fleet overlays compare streams visually and never create shared limits."
)

validation_results = validate_all_data_files(DATA_DIR)
with st.expander("Data generation and schema validation"):
    controls = st.columns(2)
    with controls[0]:
        if st.button("Regenerate sample data", type="primary"):
            outputs = generate_all_sample_data(output_dir=DATA_DIR, seed=RANDOM_SEED)
            st.success(f"Regenerated {len(outputs)} CSV files.")
    with controls[1]:
        if validation_passed(validation_results):
            st.success("Data schema validation passed.")
        else:
            st.error("Data schema validation failed.")
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

st.subheader("Review Workflow")
review_links = st.columns(4)
with review_links[0]:
    st.page_link("pages/1_Tool_Health_Summary.py", label="Tool Health")
with review_links[1]:
    st.page_link("pages/2_Thickness_Monitor.py", label="Thickness SPC")
with review_links[2]:
    st.page_link("pages/3_Particle_Alerts.py", label="Particle Alerts")
with review_links[3]:
    st.page_link("pages/4_Excursion_Review.py", label="Excursion Review")

st.caption("Synthetic deterministic review aid; not a production disposition or automated diagnosis system.")
