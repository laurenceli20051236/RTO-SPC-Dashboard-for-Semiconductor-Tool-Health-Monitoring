from __future__ import annotations

import re

import pandas as pd
import plotly.graph_objects as go

from rto_spc.config import LEGACY_METRIC_ALIASES
from rto_spc.particle_rules import PARTICLE_REPEATED_EVENT_ESCALATION, PARTICLE_THRESHOLDS
from rto_spc.spc_rules import THICKNESS_MR_SPIKE

SPC_MARKER_CODES = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
SPC_STREAM_COLORS = [
    "#1f77b4",
    "#d62728",
    "#2ca02c",
    "#9467bd",
    "#ff7f0e",
    "#17becf",
    "#8c564b",
    "#7f7f7f",
]


def _empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=title, template="plotly_white", height=420)
    return fig


def _flag_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df:
        return pd.Series(False, index=df.index)
    return df[column].fillna(False).astype(bool)


def _stream_key_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in ["tool_id", "chamber_id", "recipe_group", "metric_name"] if column in df.columns]


def _display_tool_id(tool_id: object) -> str:
    value = str(tool_id)
    match = re.fullmatch(r"RTO_A(\d+)", value)
    if match:
        return f"RTO_{int(match.group(1)):02d}"
    return value


def _display_chamber_id(chamber_id: object) -> str:
    value = str(chamber_id)
    match = re.fullmatch(r"CH(\d+)", value)
    if match:
        return f"Ch_{chr(ord('A') + int(match.group(1)) - 1)}"
    return value


def _stream_label(row: pd.Series) -> str:
    return f"{_display_tool_id(row.get('tool_id'))}_{_display_chamber_id(row.get('chamber_id'))}"


def _fleet_thickness_columns(metric_name: str) -> tuple[list[str], str, str, str, str, str]:
    if metric_name == "thickness_rtr_mean":
        return ["thickness_rtr_mean", "rtr_mean"], "value", "ucl", "cl", "lcl", "RTR Mean"
    if metric_name == "thickness_sigma":
        return ["thickness_sigma", "sigma"], "value", "ucl", "cl", "lcl", "SIGMA"
    if metric_name == "thickness_xbar":
        return ["thickness_xbar", "xbar", "thickness_mean"], "value", "ucl", "cl", "lcl", "X-BAR"
    if metric_name == "thickness_wiw_stdev":
        return ["thickness_wiw_stdev", "wiw_stdev"], "value", "ucl", "cl", "lcl", "WIW Stdev"
    if metric_name == "rtr_mean":
        return ["thickness_rtr_mean", "rtr_mean"], "value", "ucl", "cl", "lcl", "RTR Mean"
    if metric_name == "sigma":
        return ["thickness_sigma", "sigma"], "value", "ucl", "cl", "lcl", "SIGMA"
    if metric_name == "xbar":
        return ["thickness_xbar", "xbar", "thickness_mean"], "value", "ucl", "cl", "lcl", "X-BAR"
    if metric_name == "wiw_stdev":
        return ["thickness_wiw_stdev", "wiw_stdev"], "value", "ucl", "cl", "lcl", "WIW Stdev"
    return [metric_name], "value", "ucl", "cl", "lcl", metric_name


def _particle_label(metric_name: str) -> str:
    labels = {
        "particle_total_adder": "Total Adder",
        "particle_cluster_adder": "Cluster Adder",
        "particle_large_adder": "Large Adder",
        "total_adder": "Total Adder",
        "cluster_adder": "Cluster Adder",
        "large_particle_adder": "Large Adder",
    }
    return labels.get(metric_name, metric_name)


def _rule_mask(df: pd.DataFrame, rule_name: str) -> pd.Series:
    if "rule_triggered" not in df:
        return pd.Series(False, index=df.index)
    return df["rule_triggered"].fillna("").astype(str).str.contains(rule_name, regex=False)


def _format_limit_value(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.4f}"


def _limit_summary(df: pd.DataFrame, column: str, label: str) -> str:
    if column not in df or df[column].dropna().empty:
        return ""
    values = sorted({round(float(value), 4) for value in df[column].dropna()})
    if len(values) == 1:
        return f"{label}={values[0]:.4f}"
    return f"{label}={values[0]:.4f}-{values[-1]:.4f}"


def _weekly_pm_points(df: pd.DataFrame, max_weeks: int = 14) -> pd.DataFrame:
    if df.empty:
        return df

    ordered = df.copy()
    ordered["timestamp"] = pd.to_datetime(ordered["timestamp"])
    start = ordered["timestamp"].min().normalize()
    ordered["_week_index"] = ((ordered["timestamp"].dt.normalize() - start).dt.days // 7) + 1
    ordered = ordered[(ordered["_week_index"] >= 1) & (ordered["_week_index"] <= max_weeks)].copy()
    if ordered.empty:
        return ordered

    if "_event_flag" not in ordered:
        ordered["_event_flag"] = False
    ordered["_event_flag"] = ordered["_event_flag"].fillna(False).astype(bool)
    group_columns = [column for column in ["tool_id", "chamber_id", "metric_name", "_week_index"] if column in ordered.columns]
    weekly_rows = []
    for _, group in ordered.groupby(group_columns, sort=False, dropna=False):
        weekly_rows.append(group.sort_values(["_event_flag", "timestamp"]).iloc[-1])
    weekly = pd.DataFrame(weekly_rows).reset_index(drop=True)
    weekly["_week_label"] = weekly["_week_index"].map(lambda week: f"W{int(week):02d}")
    return weekly.sort_values(["_week_index", "tool_id", "chamber_id", "recipe_group"]).reset_index(drop=True)


def _prepare_letter_chart_df(df: pd.DataFrame, *, max_weeks: int = 14) -> pd.DataFrame:
    ordered = df.copy()
    ordered["timestamp"] = pd.to_datetime(ordered["timestamp"])
    ordered = _weekly_pm_points(ordered, max_weeks=max_weeks)
    if ordered.empty:
        return ordered

    stream_columns = [column for column in ["tool_id", "chamber_id"] if column in ordered.columns]
    streams = ordered[stream_columns].drop_duplicates().sort_values(stream_columns).reset_index(drop=True)
    stream_codes: dict[tuple[object, ...], str] = {}
    stream_colors: dict[tuple[object, ...], str] = {}
    for index, row in streams.iterrows():
        key = tuple(row[column] for column in stream_columns)
        stream_codes[key] = SPC_MARKER_CODES[index % len(SPC_MARKER_CODES)]
        stream_colors[key] = SPC_STREAM_COLORS[index % len(SPC_STREAM_COLORS)]

    ordered["_stream_key"] = ordered[stream_columns].apply(lambda row: tuple(row[column] for column in stream_columns), axis=1)
    ordered["_stream_code"] = ordered["_stream_key"].map(stream_codes)
    ordered["_stream_color"] = ordered["_stream_key"].map(stream_colors)
    ordered["_stream_legend"] = ordered.apply(
        lambda row: f"{row['_stream_code']} {_stream_label(row)}",
        axis=1,
    )
    return ordered.sort_values("_week_index")


def _add_paper_limit_traces(fig: go.Figure, ordered: pd.DataFrame, limit_columns: list[tuple[str, str, str]]) -> None:
    group_columns = [column for column in ["tool_id", "chamber_id", "metric_name"] if column in ordered.columns]
    seen_limit_series: set[tuple[str, tuple[float, ...]]] = set()
    for _, group in ordered.groupby(group_columns, sort=False, dropna=False):
        stream_label = str(group["_stream_legend"].iloc[0]) if "_stream_legend" in group else _stream_label(group.iloc[0])
        for column, label, dash in limit_columns:
            if column in group and group[column].notna().any():
                y_values = tuple(round(float(value), 6) for value in group[column].dropna())
                series_key = (column, y_values)
                if series_key in seen_limit_series:
                    continue
                seen_limit_series.add(series_key)
                fig.add_trace(
                    go.Scatter(
                        x=group["_week_index"],
                        y=group[column],
                        mode="lines",
                        name=f"{stream_label} {label}",
                        legendgroup=stream_label,
                        showlegend=False,
                        line=dict(color="#111111", dash=dash, width=1.4),
                        hovertemplate=f"Week=%{{x}}<br>{label}: %{{y:.4f}}<extra>{stream_label}</extra>",
                    )
                )


def _add_right_limit_labels(fig: go.Figure, df: pd.DataFrame, limit_columns: list[tuple[str, str, str]]) -> None:
    group_columns = [column for column in ["tool_id", "chamber_id", "metric_name"] if column in df.columns]
    grouped = df.groupby(group_columns, sort=False, dropna=False) if group_columns else [(None, df)]
    seen_limit_labels: set[tuple[str, float]] = set()
    for _, group in grouped:
        for column, label, _dash in limit_columns:
            if column not in group or group[column].dropna().empty:
                continue
            y_value = float(group[column].dropna().iloc[-1])
            label_key = (column, round(y_value, 6))
            if label_key in seen_limit_labels:
                continue
            seen_limit_labels.add(label_key)
            fig.add_annotation(
                x=14.28,
                y=y_value,
                xref="x",
                yref="y",
                text=f"<b>{label}</b>",
                showarrow=False,
                xanchor="left",
                font=dict(color="#111111", size=12),
            )


def _apply_paper_spc_layout(
    fig: go.Figure,
    *,
    title: str,
    yaxis_title: str,
    note: str,
    height: int = 470,
    note_intro: str = "Weekly PM display shows the first 14 weeks only; control limits are baseline-only golden-tool reference limits where available",
) -> go.Figure:
    fig.update_layout(
        title=title,
        xaxis_title="WEEK",
        yaxis_title=yaxis_title.upper(),
        template="plotly_white",
        height=height,
        plot_bgcolor="#fffdf8",
        paper_bgcolor="#fffdf8",
        font=dict(color="#111111", family="Arial"),
        margin=dict(l=78, r=185, t=55, b=125),
        legend=dict(title="URailer", x=1.03, y=1.0, xanchor="left", yanchor="top", bgcolor="rgba(255,255,255,0)"),
    )
    fig.update_xaxes(
        range=[0.5, 14.55],
        tickmode="array",
        tickvals=list(range(1, 15)),
        ticktext=[f"W{week:02d}" for week in range(1, 15)],
        tickangle=0,
        showline=True,
        linecolor="#111111",
        linewidth=1.5,
        mirror=True,
        ticks="outside",
        showgrid=True,
        gridcolor="#ddd8cf",
    )
    fig.update_yaxes(showline=True, linecolor="#111111", linewidth=1.5, mirror=True, ticks="outside", showgrid=True, gridcolor="#e8e3da")
    if note:
        fig.add_annotation(
            x=0.5,
            y=-0.29,
            xref="paper",
            yref="paper",
            text=f"<i>Note: {note_intro}</i><br>{note}",
            showarrow=False,
            align="center",
            font=dict(size=12, color="#111111"),
        )
    return fig


def _paper_spc_letter_chart(
    df: pd.DataFrame,
    *,
    title: str,
    value_column: str,
    yaxis_title: str,
    limit_columns: list[tuple[str, str, str]],
    event_mask: pd.Series | None = None,
    note_parts: list[str] | None = None,
    height: int = 470,
) -> go.Figure:
    if df.empty or value_column not in df:
        return _empty_figure(title)

    chart_df = df.copy()
    if event_mask is not None:
        chart_df["_event_flag"] = pd.Series(event_mask, index=df.index).fillna(False).astype(bool)
    ordered = _prepare_letter_chart_df(chart_df)
    fig = go.Figure()
    for stream_label, group in ordered.groupby("_stream_legend", sort=False):
        stream_color = str(group["_stream_color"].iloc[0])
        fig.add_trace(
            go.Scatter(
                x=group["_week_index"],
                y=group[value_column],
                mode="text",
                text=group["_stream_code"],
                name=stream_label,
                legendgroup=stream_label,
                textfont=dict(color=stream_color, size=14, family="Arial Black"),
                hovertemplate=(
                    "Week=%{x}<br>"
                    "Date=%{customdata}<br>"
                    f"{yaxis_title}=%{{y:.4f}}<br>"
                    f"{stream_label}<extra></extra>"
                ),
                customdata=group["timestamp"].dt.strftime("%Y-%m-%d"),
            )
        )

    _add_paper_limit_traces(fig, ordered, limit_columns)

    if "_event_flag" in ordered:
        events = ordered[ordered["_event_flag"].fillna(False).astype(bool)]
        for stream_label, group in events.groupby("_stream_legend", sort=False):
            stream_color = str(group["_stream_color"].iloc[0])
            fig.add_trace(
                go.Scatter(
                    x=group["_week_index"],
                    y=group[value_column],
                    mode="text",
                    text=group["_stream_code"],
                    name=f"{stream_label} Events",
                    legendgroup=stream_label,
                    showlegend=False,
                    textfont=dict(color=stream_color, size=18, family="Arial Black"),
                    hovertemplate=(
                        "Event Week=%{x}<br>"
                        "Date=%{customdata}<br>"
                        f"{yaxis_title}=%{{y:.4f}}<br>"
                        f"{stream_label}<extra>Event</extra>"
                    ),
                    customdata=group["timestamp"].dt.strftime("%Y-%m-%d"),
                )
            )

    _add_right_limit_labels(fig, ordered, limit_columns)
    note = ", ".join(part for part in (note_parts or []) if part)
    return _apply_paper_spc_layout(fig, title=title, yaxis_title=yaxis_title, note=note, height=height)


def _paper_particle_threshold_chart(df: pd.DataFrame, metric_name: str, title: str) -> go.Figure:
    if df.empty:
        return _empty_figure(title)

    threshold_metric_name = LEGACY_METRIC_ALIASES.get(metric_name, metric_name)
    thresholds = PARTICLE_THRESHOLDS[threshold_metric_name]
    chart_df = df.copy()
    severity = chart_df.get("severity", pd.Series("", index=chart_df.index)).fillna("")
    rules = chart_df.get("rule_triggered", pd.Series("", index=chart_df.index)).fillna("").astype(str)
    chart_df["_event_flag"] = severity.isin(["Medium", "High"]) | rules.str.contains(PARTICLE_REPEATED_EVENT_ESCALATION, regex=False)
    ordered = _prepare_letter_chart_df(chart_df)
    fig = go.Figure()
    for stream_label, group in ordered.groupby("_stream_legend", sort=False):
        stream_color = str(group["_stream_color"].iloc[0])
        fig.add_trace(
            go.Scatter(
                x=group["_week_index"],
                y=group["value"],
                mode="text",
                text=group["_stream_code"],
                name=stream_label,
                legendgroup=stream_label,
                textfont=dict(color=stream_color, size=14, family="Arial Black"),
                hovertemplate=("Week=%{x}<br>Date=%{customdata}<br>Adder Count=%{y:.4f}<br>" f"{stream_label}<extra></extra>"),
                customdata=group["timestamp"].dt.strftime("%Y-%m-%d"),
            )
        )

        medium = group[group.get("severity", "").fillna("").eq("Medium")]
        high = group[group.get("severity", "").fillna("").eq("High")]
        repeated = group[group.get("rule_triggered", "").fillna("").astype(str).str.contains(PARTICLE_REPEATED_EVENT_ESCALATION, regex=False)]
        if not medium.empty:
            fig.add_trace(
                go.Scatter(
                    x=medium["_week_index"],
                    y=medium["value"],
                    mode="text",
                    text=medium["_stream_code"],
                    name=f"{stream_label} Medium",
                    legendgroup=stream_label,
                    showlegend=False,
                    textfont=dict(color=stream_color, size=17, family="Arial Black"),
                )
            )
        if not high.empty:
            fig.add_trace(
                go.Scatter(
                    x=high["_week_index"],
                    y=high["value"],
                    mode="text",
                    text=high["_stream_code"],
                    name=f"{stream_label} High",
                    legendgroup=stream_label,
                    showlegend=False,
                    textfont=dict(color=stream_color, size=18, family="Arial Black"),
                )
            )
        if not repeated.empty:
            fig.add_trace(
                go.Scatter(
                    x=repeated["_week_index"],
                    y=repeated["value"],
                    mode="text",
                    text=repeated["_stream_code"],
                    name=f"{stream_label} Repeated escalation",
                    legendgroup=stream_label,
                    showlegend=False,
                    textfont=dict(color=stream_color, size=20, family="Arial Black"),
                )
            )

    fig.add_hline(y=thresholds["high"], line_dash="dot", line_color="#111111", annotation_text=None)
    fig.add_hline(y=thresholds["warning"], line_dash="solid", line_color="#111111", annotation_text=None)
    for y_value, label in [(thresholds["high"], "High"), (thresholds["warning"], "Warning")]:
        fig.add_annotation(
            x=14.28,
            y=y_value,
            xref="x",
            yref="y",
            text=f"<b>{label}</b>",
            showarrow=False,
            xanchor="left",
            font=dict(color="#111111", size=12),
        )
    note = f"Warning={_format_limit_value(thresholds['warning'])}, High={_format_limit_value(thresholds['high'])}"
    return _apply_paper_spc_layout(
        fig,
        title=title,
        yaxis_title="Adder Count",
        note=note,
        height=500,
        note_intro="Weekly PM display shows the first 14 weeks only; particle limits are fixed Warning/High thresholds",
    )


def plot_fleet_thickness_trend(df: pd.DataFrame, metric_name: str) -> go.Figure:
    aliases, value_column, ucl_column, cl_column, lcl_column, label = _fleet_thickness_columns(metric_name)
    title = f"Fleet {label} Trend"
    if df.empty:
        return _empty_figure(title)

    metric_df = df[df["metric_name"].isin(aliases)].copy()
    if metric_df.empty or value_column not in metric_df:
        return _empty_figure(title)

    event_mask = _flag_series(metric_df, "warning_flag") | _flag_series(metric_df, "ooc_flag")

    limit_columns = [(ucl_column, "UCL", "dot"), (cl_column, "CL", "solid"), (lcl_column, "LCL", "dot")]
    note_parts = [_limit_summary(metric_df, lcl_column, "LCL"), _limit_summary(metric_df, ucl_column, "UCL"), _limit_summary(metric_df, cl_column, "CL")]
    return _paper_spc_letter_chart(
        metric_df,
        title=title,
        value_column=value_column,
        yaxis_title=label,
        limit_columns=limit_columns,
        event_mask=event_mask,
        note_parts=note_parts,
        height=500,
    )


def plot_fleet_particle_trend(df: pd.DataFrame, metric_name: str) -> go.Figure:
    title = f"Fleet {_particle_label(metric_name)} Trend"
    if df.empty:
        return _empty_figure(title)

    metric_df = df[(df["monitor_type"] == "Particle") & (df["metric_name"] == metric_name)].copy()
    if metric_df.empty:
        return _empty_figure(title)

    return _paper_particle_threshold_chart(metric_df, metric_name, title)


def plot_selected_thickness_stream(
    df: pd.DataFrame,
    events_df: pd.DataFrame,
    tool_id: str,
    chamber_id: str,
    recipe_group: str,
    metric_name: str,
) -> go.Figure:
    selected = df[
        (df["tool_id"] == tool_id)
        & (df["chamber_id"] == chamber_id)
        & (df["recipe_group"] == recipe_group)
        & (df["metric_name"] == metric_name)
    ].copy()
    if selected.empty:
        return _empty_figure("Selected Thickness Stream")

    event_ids = set()
    if events_df is not None and not events_df.empty and "measurement_id" in events_df:
        matching = events_df[
            (events_df["tool_id"] == tool_id)
            & (events_df["chamber_id"] == chamber_id)
            & (events_df["recipe_group"] == recipe_group)
            & (events_df["metric_name"] == metric_name)
        ]
        event_ids = set(matching["measurement_id"].dropna().astype(str))
    selected["_event_flag"] = selected.get("measurement_id", pd.Series("", index=selected.index)).astype(str).isin(event_ids)
    label = _fleet_thickness_columns(metric_name)[5]
    return plot_primary_thickness_spc_chart(selected, title=f"Selected {label} Stream", value_label=label)


def plot_selected_particle_stream(
    df: pd.DataFrame,
    events_df: pd.DataFrame,
    tool_id: str,
    chamber_id: str,
    recipe_group: str,
    metric_name: str,
) -> go.Figure:
    _ = events_df
    selected = df[
        (df["tool_id"] == tool_id)
        & (df["chamber_id"] == chamber_id)
        & (df["recipe_group"] == recipe_group)
        & (df["metric_name"] == metric_name)
    ].copy()
    if selected.empty:
        return _empty_figure("Selected Particle Stream")
    return _paper_particle_threshold_chart(selected, metric_name, f"Selected {_particle_label(metric_name)} Stream")


def plot_fleet_tool_health_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure("Fleet Tool Health Score")

    ordered = df.sort_values("tool_id").copy()
    color_map = {"Healthy": "#2ca02c", "Watch": "#ffbf00", "Warning": "#ff7f0e", "Critical": "#d62728"}
    colors = [color_map.get(status, "#4c78a8") for status in ordered["status"]]
    display_score = ordered["health_score"].astype(float).copy()
    event_count = ordered.get("event_count", pd.Series(0, index=ordered.index)).fillna(0).astype(int)
    display_score = display_score.mask((display_score == 0) & (event_count > 0), 3.0)
    labels = ordered.apply(lambda row: f"{row['status']} ({float(row['health_score']):.1f})", axis=1)
    for column, default in [("starting_score", 100.0), ("penalty_points", 100.0), ("high_events", 0), ("medium_events", 0)]:
        if column not in ordered:
            ordered[column] = default
    customdata = ordered[["health_score", "starting_score", "penalty_points", "status", "event_count", "high_events", "medium_events"]].to_numpy()
    fig = go.Figure(
        go.Bar(
            x=display_score,
            y=ordered["tool_id"],
            orientation="h",
            marker_color=colors,
            text=labels,
            textposition="outside",
            customdata=customdata,
            hovertemplate=(
                "Tool=%{y}<br>"
                "Health score=%{customdata[0]}<br>"
                "Starting score=%{customdata[1]}<br>"
                "Penalty points=%{customdata[2]}<br>"
                "Status=%{customdata[3]}<br>"
                "Events=%{customdata[4]}<br>"
                "High=%{customdata[5]}<br>"
                "Medium=%{customdata[6]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title="Fleet Tool Health Score",
        xaxis_title="Health Score",
        yaxis_title="Tool",
        xaxis_range=[0, 110],
        template="plotly_white",
        height=420,
        margin=dict(l=90, r=110, t=55, b=85),
    )
    fig.add_annotation(
        x=0.5,
        y=-0.23,
        xref="paper",
        yref="paper",
        text="Score starts at 100 and decreases by weighted recent events; zero-score tools use a small floor bar only for visibility.",
        showarrow=False,
        font=dict(size=11, color="#6b7280"),
    )
    return fig


def plot_fleet_event_count_bar(events_df: pd.DataFrame, group_by: str | list[str] = "metric_name", title: str | None = None) -> go.Figure:
    keys = [group_by] if isinstance(group_by, str) else list(group_by)
    chart_title = title or f"Fleet Event Count by {' / '.join(keys)}"
    if events_df.empty:
        return _empty_figure(chart_title)

    summary = events_df.groupby(keys, dropna=False).size().reset_index(name="event_count")
    summary = summary.sort_values("event_count", ascending=False)
    if len(keys) == 1:
        summary["category"] = summary[keys[0]].astype(str)
    else:
        summary["category"] = summary[keys].astype(str).agg(" / ".join, axis=1)
    fig = go.Figure(go.Bar(x=summary["category"], y=summary["event_count"], customdata=summary[keys].astype(str).to_numpy(), text=summary["event_count"], textposition="outside"))
    fig.update_layout(title=chart_title, xaxis_title=" / ".join(keys), yaxis_title="Event Count", template="plotly_white", height=420)
    return fig


def plot_severity_distribution(events_df: pd.DataFrame) -> go.Figure:
    return plot_fleet_event_count_bar(events_df, group_by="severity", title="Severity Distribution")


def plot_fleet_excursion_timeline(events_df: pd.DataFrame) -> go.Figure:
    if events_df.empty:
        return _empty_figure("Fleet Excursion Timeline")

    ordered = events_df.copy()
    ordered["timestamp"] = pd.to_datetime(ordered["timestamp"])
    ordered["stream"] = ordered[["tool_id", "chamber_id", "metric_name"]].astype(str).agg(" / ".join, axis=1)
    fig = go.Figure()
    for severity, color in [("Medium", "#ff7f0e"), ("High", "#d62728")]:
        subset = ordered[ordered["severity"] == severity]
        if not subset.empty:
            fig.add_trace(go.Scatter(x=subset["timestamp"], y=subset["stream"], mode="markers", name=severity, marker=dict(color=color, size=10)))
    fig.update_layout(title="Fleet Excursion Timeline", xaxis_title="Timestamp", yaxis_title="Tool / Chamber / Metric", template="plotly_white", height=460)
    return fig


def plot_primary_thickness_spc_chart(df: pd.DataFrame, *, title: str, value_label: str = "Value") -> go.Figure:
    if df.empty:
        return _empty_figure(title)

    event_mask = _flag_series(df, "warning_flag") | _flag_series(df, "ooc_flag")
    limit_columns = [("ucl", "UCL", "dot"), ("cl", "CL", "solid"), ("lcl", "LCL", "dot")]
    note_parts = [_limit_summary(df, "lcl", "LCL"), _limit_summary(df, "ucl", "UCL"), _limit_summary(df, "cl", "CL")]
    return _paper_spc_letter_chart(
        df,
        title=title,
        value_column="value",
        yaxis_title=value_label,
        limit_columns=limit_columns,
        event_mask=event_mask,
        note_parts=note_parts,
    )


def plot_thickness_imr_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure("Thickness Individual Chart")

    event_mask = _flag_series(df, "ooc_flag")
    limit_columns = [("ucl", "UCL", "dot"), ("cl", "CL", "solid"), ("lcl", "LCL", "dot")]
    note_parts = [_limit_summary(df, "lcl", "LCL"), _limit_summary(df, "ucl", "UCL"), _limit_summary(df, "cl", "CL")]
    return _paper_spc_letter_chart(
        df,
        title="Thickness Individual Chart",
        value_column="value",
        yaxis_title="Value",
        limit_columns=limit_columns,
        event_mask=event_mask,
        note_parts=note_parts,
    )


def plot_moving_range_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure("Thickness Moving Range Chart")

    ordered = df.sort_values("timestamp")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ordered["timestamp"], y=ordered["mr_value"], mode="lines+markers", name="MR"))

    for column, label, color in [("mr_ucl", "MR_UCL", "#d62728"), ("mr_cl", "MR_CL", "#2ca02c"), ("mr_lcl", "MR_LCL", "#9467bd")]:
        if column in ordered and ordered[column].notna().any():
            fig.add_trace(go.Scatter(x=ordered["timestamp"], y=ordered[column], mode="lines", name=label, line=dict(color=color, dash="dash")))

    events = ordered[ordered.get("rule_triggered", "").fillna("").astype(str).str.contains(THICKNESS_MR_SPIKE, regex=False)]
    if not events.empty:
        fig.add_trace(go.Scatter(x=events["timestamp"], y=events["mr_value"], mode="markers", name="MR spike", marker=dict(color="#ff7f0e", size=11, symbol="diamond")))

    fig.update_layout(title="Thickness Moving Range Chart", xaxis_title="Timestamp", yaxis_title="Moving Range", template="plotly_white", height=420)
    return fig


def plot_particle_threshold_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure("Particle Threshold Chart")

    metric_name = str(df["metric_name"].iloc[0])
    return _paper_particle_threshold_chart(df, metric_name, "Particle Threshold Chart")


def plot_tool_health_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure("Tool Health")

    color_map = {"Healthy": "#2ca02c", "Watch": "#ffbf00", "Warning": "#ff7f0e", "Critical": "#d62728"}
    colors = [color_map.get(status, "#4c78a8") for status in df["status"]]
    fig = go.Figure(go.Bar(x=df["tool_id"], y=df["health_score"], marker_color=colors, text=df["status"], textposition="outside"))
    fig.update_layout(title="Synthetic Demo Tool Health Score", xaxis_title="Tool", yaxis_title="Health Score", yaxis_range=[0, 110], template="plotly_white", height=420)
    return fig


def plot_excursion_timeline(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure("Excursion Timeline")

    ordered = df.sort_values("timestamp")
    fig = go.Figure()
    for severity, color in [("Medium", "#ff7f0e"), ("High", "#d62728")]:
        subset = ordered[ordered["severity"] == severity]
        if not subset.empty:
            fig.add_trace(go.Scatter(x=subset["timestamp"], y=subset["metric_name"], mode="markers", name=severity, marker=dict(color=color, size=10)))
    fig.update_layout(title="Excursion Timeline", xaxis_title="Timestamp", yaxis_title="Metric", template="plotly_white", height=420)
    return fig
