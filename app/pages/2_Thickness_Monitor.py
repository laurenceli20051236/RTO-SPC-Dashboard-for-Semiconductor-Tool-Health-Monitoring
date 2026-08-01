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
    plot_fleet_thickness_trend,
    plot_selected_thickness_stream,
)
from rto_spc.config import THICKNESS_METRICS
from rto_spc.data_loader import load_excursion_events, load_spc_results

st.set_page_config(page_title="RTO Thickness Monitor", layout="wide")
st.title("RTO Thickness Monitor")

spc = load_spc_results()
events = load_excursion_events()
thickness = spc[(spc["monitor_type"] == "Thickness") & (spc["metric_name"].isin(THICKNESS_METRICS))] if not spc.empty else spc
thickness_events = events[(events["monitor_type"] == "Thickness") & (events["metric_name"].isin(THICKNESS_METRICS))] if not events.empty else events

if thickness.empty:
    st.warning("No Thickness data loaded. Run `python scripts/generate_sample_data.py`.")
else:
    recipe_group_options = ["RTO_Fleet"] + sorted(thickness["recipe_group"].dropna().unique().tolist())
    tool_options = ["RTO_Fleet"] + sorted(thickness["tool_id"].dropna().unique().tolist())
    fleet_filters = st.columns(2)
    with fleet_filters[0]:
        fleet_recipe_group = st.selectbox("fleet_recipe_group", recipe_group_options)
    with fleet_filters[1]:
        default_tool_index = tool_options.index("RTO_A01") if "RTO_A01" in tool_options else 0
        fleet_tool_id = st.selectbox("fleet_tool_id", tool_options, index=default_tool_index)

    fleet_source = thickness if fleet_recipe_group == "RTO_Fleet" else thickness[thickness["recipe_group"] == fleet_recipe_group]
    fleet_events = thickness_events if fleet_recipe_group == "RTO_Fleet" else thickness_events[thickness_events["recipe_group"] == fleet_recipe_group]
    if fleet_tool_id != "RTO_Fleet":
        fleet_source = fleet_source[fleet_source["tool_id"] == fleet_tool_id]
        fleet_events = fleet_events[fleet_events["tool_id"] == fleet_tool_id]

    st.subheader("Fleet Overview")
    st.caption("Fleet overlay is chamber-level when a tool is selected, e.g. RTO_01_Ch_A and RTO_01_Ch_B.")
    top_left, top_right = st.columns(2)
    with top_left:
        st.plotly_chart(plot_fleet_thickness_trend(fleet_source, "thickness_rtr_mean"), use_container_width=True)
    with top_right:
        st.plotly_chart(plot_fleet_thickness_trend(fleet_source, "thickness_xbar"), use_container_width=True)

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(plot_fleet_thickness_trend(fleet_source, "thickness_wiw_stdev"), use_container_width=True)
    with bottom_right:
        st.plotly_chart(plot_fleet_thickness_trend(fleet_source, "thickness_sigma"), use_container_width=True)

    st.plotly_chart(
        plot_fleet_event_count_bar(fleet_events, group_by=["tool_id", "chamber_id", "metric_name"], title="Thickness Event Count by Tool / Chamber / Metric"),
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

    metric_name = st.selectbox("metric_name", THICKNESS_METRICS)
    st.plotly_chart(plot_selected_thickness_stream(thickness, thickness_events, tool_id, chamber_id, recipe_group, metric_name), use_container_width=True)

    st.subheader("Event Table")
    selected_events = thickness_events[
        (thickness_events["tool_id"] == tool_id)
        & (thickness_events["chamber_id"] == chamber_id)
        & (thickness_events["recipe_group"] == recipe_group)
        & (thickness_events["metric_name"] == metric_name)
    ] if not thickness_events.empty else thickness_events
    st.dataframe(selected_events, use_container_width=True, hide_index=True)

    st.subheader("Methodology Note")
    st.write(
        "RTO thickness monitor uses module-level synthetic metrics: RTR Mean, X-BAR, WIW Stdev, and SIGMA. "
        "Limits are calculated from baseline data only for each tool/chamber/recipe/metric stream."
    )
