from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rto_spc.data_loader import load_excursion_events

DISCLAIMER = "This summary is generated from deterministic SPC / threshold results and does not replace engineering review."

st.set_page_config(page_title="Local Event Summary", layout="wide")
st.title("Local Event Summary")
st.info(DISCLAIMER)

events = load_excursion_events()

if events.empty:
    st.warning("No excursion events loaded. Run `python scripts/generate_sample_data.py`.")
else:
    st.subheader("Event Selector")
    event_id = st.selectbox("event_id", events["event_id"].dropna().astype(str).tolist())
    selected = events[events["event_id"].astype(str) == event_id].iloc[0]

    st.subheader("Selected Event Details")
    st.dataframe(selected.astype(str).to_frame(name="value"), use_container_width=True)

    st.subheader("Local Deterministic Summary")
    st.write(
        f"{selected['event_id']} is a {selected['severity']} {selected['monitor_type']} event for "
        f"{selected['tool_id']} / {selected['chamber_id']} / {selected['recipe_group']} on "
        f"{selected['metric_name']}. Rule triggered: {selected['rule_triggered']}. "
        f"Suggested review area: {selected['suggested_review_area']}"
    )

    st.subheader("Methodology Note")
    st.write(DISCLAIMER)
