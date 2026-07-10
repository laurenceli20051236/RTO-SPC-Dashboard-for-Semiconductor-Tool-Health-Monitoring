from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rto_spc.chart_helpers import (
    plot_fleet_event_count_bar,
    plot_fleet_particle_trend,
    plot_selected_particle_stream,
)
from rto_spc.config import PARTICLE_METRICS
from rto_spc.data_loader import load_excursion_events, load_spc_results

st.set_page_config(page_title="Particle Alerts", layout="wide")
st.title("Particle Alerts")

spc = load_spc_results()
events = load_excursion_events()
particle = spc[(spc["monitor_type"] == "Particle") & (spc["metric_name"].isin(PARTICLE_METRICS))] if not spc.empty else spc
particle_events = events[(events["monitor_type"] == "Particle") & (events["metric_name"].isin(PARTICLE_METRICS))] if not events.empty else events

if particle.empty:
    st.warning("No Particle data loaded. Run `python scripts/generate_sample_data.py`.")
else:
    recipe_group_options = ["RTO_Fleet"] + sorted(particle["recipe_group"].dropna().unique().tolist())
    tool_options = ["RTO_Fleet"] + sorted(particle["tool_id"].dropna().unique().tolist())
    fleet_filters = st.columns(2)
    with fleet_filters[0]:
        fleet_recipe_group = st.selectbox("fleet_recipe_group", recipe_group_options)
    with fleet_filters[1]:
        default_tool_index = tool_options.index("RTO_A01") if "RTO_A01" in tool_options else 0
        fleet_tool_id = st.selectbox("fleet_tool_id", tool_options, index=default_tool_index)

    fleet_source = particle if fleet_recipe_group == "RTO_Fleet" else particle[particle["recipe_group"] == fleet_recipe_group]
    fleet_events = particle_events if fleet_recipe_group == "RTO_Fleet" else particle_events[particle_events["recipe_group"] == fleet_recipe_group]
    if fleet_tool_id != "RTO_Fleet":
        fleet_source = fleet_source[fleet_source["tool_id"] == fleet_tool_id]
        fleet_events = fleet_events[fleet_events["tool_id"] == fleet_tool_id]

    st.subheader("Fleet Overview")
    st.caption("Fleet overlay is chamber-level when a tool is selected, e.g. RTO_01_Ch_A and RTO_01_Ch_B.")
    first, second, third = st.columns(3)
    with first:
        st.plotly_chart(plot_fleet_particle_trend(fleet_source, "particle_total_adder"), use_container_width=True)
    with second:
        st.plotly_chart(plot_fleet_particle_trend(fleet_source, "particle_cluster_adder"), use_container_width=True)
    with third:
        st.plotly_chart(plot_fleet_particle_trend(fleet_source, "particle_large_adder"), use_container_width=True)

    st.plotly_chart(
        plot_fleet_event_count_bar(fleet_events, group_by=["tool_id", "chamber_id", "metric_name"], title="Particle Event Count by Tool / Chamber / Metric"),
        use_container_width=True,
    )

    st.subheader("Selected Stream Detail")
    selectable = fleet_source[["tool_id", "chamber_id", "recipe_group", "metric_name"]].drop_duplicates()
    detail_filters = st.columns(3)
    with detail_filters[0]:
        tool_id = st.selectbox("tool_id", sorted(selectable["tool_id"].dropna().unique().tolist()))
    with detail_filters[1]:
        chamber_options = sorted(selectable[selectable["tool_id"] == tool_id]["chamber_id"].dropna().unique().tolist())
        chamber_id = st.selectbox("chamber_id", chamber_options)
    with detail_filters[2]:
        recipe_options = sorted(selectable[(selectable["tool_id"] == tool_id) & (selectable["chamber_id"] == chamber_id)]["recipe_group"].dropna().unique().tolist())
        if fleet_recipe_group != "RTO_Fleet":
            recipe_options = [fleet_recipe_group]
        recipe_group = st.selectbox("recipe_group", recipe_options)

    metric_name = st.selectbox("metric_name", PARTICLE_METRICS)
    st.plotly_chart(plot_selected_particle_stream(particle, particle_events, tool_id, chamber_id, recipe_group, metric_name), use_container_width=True)

    st.subheader("Event Table")
    selected_events = particle_events[
        (particle_events["tool_id"] == tool_id)
        & (particle_events["chamber_id"] == chamber_id)
        & (particle_events["recipe_group"] == recipe_group)
        & (particle_events["metric_name"] == metric_name)
    ] if not particle_events.empty else particle_events
    st.dataframe(selected_events, use_container_width=True, hide_index=True)

    st.subheader("Methodology Note")
    st.write(
        "Phase 1 particle alerts use synthetic thresholds and repeated-event escalation. "
        "Count charts are not used as the primary alert method in Phase 1."
    )
