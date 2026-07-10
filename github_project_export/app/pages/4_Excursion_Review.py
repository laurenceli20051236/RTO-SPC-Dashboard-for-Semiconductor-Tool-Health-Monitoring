from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rto_spc.chart_helpers import plot_fleet_event_count_bar, plot_fleet_excursion_timeline, plot_severity_distribution
from rto_spc.data_loader import load_excursion_events

st.set_page_config(page_title="Excursion Review", layout="wide")
st.title("Excursion Review")

events = load_excursion_events()
if events.empty:
    st.warning("No excursion events loaded. Run `python scripts/generate_sample_data.py`.")
else:
    st.subheader("Fleet Overview")
    top_left, top_middle, top_right = st.columns(3)
    with top_left:
        st.plotly_chart(plot_fleet_event_count_bar(events, group_by="tool_id", title="Fleet Excursion Count by Tool"), use_container_width=True)
    with top_middle:
        st.plotly_chart(plot_fleet_event_count_bar(events, group_by="chamber_id", title="Fleet Excursion Count by Chamber"), use_container_width=True)
    with top_right:
        st.plotly_chart(plot_fleet_event_count_bar(events, group_by="metric_name", title="Fleet Excursion Count by Metric"), use_container_width=True)

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(plot_fleet_excursion_timeline(events), use_container_width=True)
    with bottom_right:
        st.plotly_chart(plot_severity_distribution(events), use_container_width=True)

    st.subheader("Full Excursion Events Table")
    st.dataframe(events, use_container_width=True, hide_index=True)

    filtered = events.copy()
    st.subheader("Selected Stream Detail")
    filters = st.columns(3)
    filter_columns = ["tool_id", "chamber_id", "recipe_group", "monitor_type", "metric_name", "severity", "rule_triggered"]
    for i, column in enumerate(filter_columns):
        with filters[i % 3]:
            options = ["All"] + sorted(filtered[column].dropna().astype(str).unique().tolist())
            selected = st.selectbox(column, options)
            if selected != "All":
                filtered = filtered[filtered[column].astype(str) == selected]

    st.download_button("Export filtered CSV", filtered.to_csv(index=False), file_name="excursion_events_filtered.csv", mime="text/csv")
    st.subheader("Event Table")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
