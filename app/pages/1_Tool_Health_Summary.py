from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rto_spc.chart_helpers import plot_fleet_event_count_bar, plot_fleet_tool_health_bar
from rto_spc.data_loader import load_excursion_events
from rto_spc.tool_health import TOOL_HEALTH_LABEL, calculate_tool_health

st.set_page_config(page_title="Tool Health Summary", layout="wide")
st.title("Tool Health Summary")
st.caption(TOOL_HEALTH_LABEL)
st.info("Synthetic demo health score, not a production disposition rule.")

events = load_excursion_events()
health = calculate_tool_health(events)

st.subheader("Fleet Overview")
st.plotly_chart(plot_fleet_tool_health_bar(health), use_container_width=True)
left, middle, right = st.columns(3)
with left:
    st.plotly_chart(plot_fleet_event_count_bar(events, group_by="tool_id", title="Event Count by Tool"), use_container_width=True)
with middle:
    st.plotly_chart(plot_fleet_event_count_bar(events, group_by="chamber_id", title="Event Count by Chamber"), use_container_width=True)
with right:
    st.plotly_chart(plot_fleet_event_count_bar(events, group_by="severity", title="Event Count by Severity"), use_container_width=True)

st.subheader("Selected Tool Detail")
st.dataframe(health, use_container_width=True, hide_index=True)

if events.empty:
    st.write("No excursion events loaded.")
else:
    detail_left, detail_right = st.columns(2)
    with detail_left:
        selected_tool = st.selectbox("tool_id", sorted(events["tool_id"].dropna().unique().tolist()))
    with detail_right:
        selected_chamber = st.selectbox("chamber_id", ["All"] + sorted(events[events["tool_id"] == selected_tool]["chamber_id"].dropna().unique().tolist()))
    selected_events = events[events["tool_id"] == selected_tool]
    if selected_chamber != "All":
        selected_events = selected_events[selected_events["chamber_id"] == selected_chamber]
    st.subheader("Selected Events")
    st.dataframe(selected_events.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)

    st.subheader("Latest High-Severity Events")
    if events.empty:
        st.write("No high-severity events loaded.")
    else:
        high = events[events["severity"] == "High"].sort_values("timestamp", ascending=False)
        st.dataframe(high.head(10), use_container_width=True, hide_index=True)
