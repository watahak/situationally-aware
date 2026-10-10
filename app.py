import streamlit as st
import importlib

st.set_page_config(
    page_title="Capital Structure Decoder",
    page_icon="\U0001f310",
    layout="wide",
    initial_sidebar_state="auto",
)

import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
from settings.app_constants import NO_DATA_MSG, ROTATION_LANES
from settings.market import CONFIG, LOOKBACK_MAP, MACRO_ANCHORS
import ui.theme as theme_utils


_THEME_MODULE_MTIME_KEY = "_theme_module_mtime"
_theme_module_mtime = Path(theme_utils.__file__).stat().st_mtime
_last_theme_module_mtime = st.session_state.get(_THEME_MODULE_MTIME_KEY)

if (
    not hasattr(theme_utils, "get_live_theme_mode")
    or (
        _last_theme_module_mtime is None
        or _last_theme_module_mtime != _theme_module_mtime
    )
):
    theme_utils = importlib.reload(theme_utils)

st.session_state[_THEME_MODULE_MTIME_KEY] = _theme_module_mtime


_THEME_MODE = theme_utils.get_live_theme_mode()
_PLOTLY_TEMPLATE = theme_utils.get_plotly_template(_THEME_MODE)
_DARK = theme_utils.get_active_palette(_THEME_MODE)
theme_utils.inject_theme_styles(_THEME_MODE)

_IS_LIGHT_THEME = _THEME_MODE == "light"
_ECHART_LINE = "rgba(15, 23, 42, 0.16)" if _IS_LIGHT_THEME else "rgba(255, 255, 255, 0.1)"
_ECHART_BORDER = "rgba(15, 23, 42, 0.18)" if _IS_LIGHT_THEME else "rgba(255, 255, 255, 0.1)"
_ECHART_CELL_BORDER = "rgba(15, 23, 42, 0.12)" if _IS_LIGHT_THEME else "rgba(255,255,255,0.06)"
_ECHART_SHADOW = "rgba(15, 23, 42, 0.22)" if _IS_LIGHT_THEME else "rgba(0,0,0,0.35)"
_ZSCORE_NEUTRAL_BAR = "rgba(100, 116, 139, 0.42)" if _IS_LIGHT_THEME else "rgba(148, 163, 184, 0.4)"
_ZSCORE_NEUTRAL_BAR_FAINT = "rgba(100, 116, 139, 0.22)" if _IS_LIGHT_THEME else "rgba(148, 163, 184, 0.2)"
_ZSCORE_BAND_NEUTRAL = "rgba(15, 23, 42, 0.06)" if _IS_LIGHT_THEME else "rgba(255, 255, 255, 0.03)"
_ZSCORE_BAND_WARNING = "rgba(217, 119, 6, 0.12)" if _IS_LIGHT_THEME else "rgba(234, 179, 8, 0.08)"
_ZSCORE_BAND_RISK = "rgba(220, 38, 38, 0.14)" if _IS_LIGHT_THEME else "rgba(239, 68, 68, 0.12)"

_CHART_LAYOUT = dict(
    template=_PLOTLY_TEMPLATE,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=_DARK["text"], family="Inter, sans-serif"),
    hoverlabel=dict(bgcolor=_DARK["slate"], font_size=13, font_family="Inter, sans-serif"),
)

from core import (
    e,
    pair_display_name,
    get_all_tickers,
    calc_roc_table,
    calc_rotation_table,
    calc_ratio,
    calc_sma,
    calc_zscore,
    calc_financialization_gap,
)


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=43200, show_spinner="Fetching market data…")
def fetch_data(tickers: tuple[str, ...], period_days: int) -> pd.DataFrame:
    """Download adjusted-close prices for all tickers via yfinance.

    Uses a single yf.download call for efficiency.  Returns a DataFrame with
    DatetimeIndex (timezone-naive) and one column per ticker.
    """
    end = datetime.now()
    start = end - timedelta(days=period_days)

    df = yf.download(
        list(tickers),
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )

    if df.empty:
        return pd.DataFrame()

    # yf.download returns MultiIndex columns (Price, Ticker) for >1 ticker
    if isinstance(df.columns, pd.MultiIndex):
        df = df["Close"]
    else:
        df = df[["Close"]].rename(columns={"Close": tickers[0]})

    # Strip timezone so comparisons with naive Timestamps work cleanly
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    return df


# ---------------------------------------------------------------------------
# Chart builders (return go.Figure — no st.* calls)
# ---------------------------------------------------------------------------

_ROTATION = {
    "surface": "rgba(0,0,0,0)",
    "text": _DARK["text"],
    "secondary": _DARK["muted"],
    "neutral": "#64748B",
    "grid": _DARK["grid"],
    "accent": _DARK["accent"],
    "lane_bg": "rgba(15, 23, 42, 0.05)" if _IS_LIGHT_THEME else "rgba(255, 255, 255, 0.025)",
    "lane_border": "rgba(15, 23, 42, 0.14)" if _IS_LIGHT_THEME else "rgba(255, 255, 255, 0.06)",
    "node_fill": _DARK["slate"],
    "node_ring": _DARK["accent"],
    "selected_glow": "rgba(2, 132, 199, 0.22)" if _IS_LIGHT_THEME else "rgba(56, 189, 248, 0.3)",
}


def _rotation_pct(value) -> str:
    if pd.isna(value):
        return "Unavailable"
    if 1e-10 < abs(value) < 0.005:
        return f"{'+' if value > 0 else '−'}<0.01%"
    return f"{value:+.2f}%"


def _rotation_date(value) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%d") if pd.notna(value) else "Unavailable"


def _rotation_direction(row, prefix: str = "") -> str:
    if row[f"{prefix}status"] != "Valid":
        return "Unavailable"
    if pd.isna(row[f"{prefix}leader"]):
        return "Flat"
    return f"{row[f'{prefix}laggard']} → {row[f'{prefix}leader']}"


def rotation_evidence_table(snapshot: pd.DataFrame) -> pd.DataFrame:
    """Format comparison details for network-link hover."""
    records = []
    for _, row in snapshot.iterrows():
        records.append({
            "Pair": row["name"],
            "Start": _rotation_date(row["start_date"]),
            "As of": _rotation_date(row["end_date"]),
            "Numerator": row["numerator"],
            "Numerator return": _rotation_pct(row["numerator_return"]),
            "Denominator": row["denominator"],
            "Denominator return": _rotation_pct(row["denominator_return"]),
            "Ratio change": _rotation_pct(row["ratio_change"]),
            "Direction": _rotation_direction(row),
            "Prior start": _rotation_date(row["previous_start_date"]),
            "Prior end": _rotation_date(row["previous_end_date"]),
            "Prior numerator return": _rotation_pct(row["previous_numerator_return"]),
            "Prior denominator return": _rotation_pct(row["previous_denominator_return"]),
            "Prior ratio change": _rotation_pct(row["previous_ratio_change"]),
            "Prior direction": _rotation_direction(row, "previous_"),
            "Transition": row["transition"],
            "Paired observations": f"{row['coverage']}/{row['expected_observations']}",
            "Prior paired observations": f"{row['previous_coverage']}/{row['expected_observations']}",
            "Data quality": row["status"],
            "Prior data quality": row["previous_status"],
            "Numerator last valid": _rotation_date(row["numerator_last_valid"]),
            "Denominator last valid": _rotation_date(row["denominator_last_valid"]),
        })
    return pd.DataFrame(records)


def build_rotation_network(
    snapshot: pd.DataFrame,
    selected_pair: str,
) -> go.Figure:
    """Fixed comparison lanes; arrowheads indicate outperformance, never flow volume."""
    c = _ROTATION
    coordinates = {}
    fig = go.Figure()

    for lane, (label, tickers) in enumerate(ROTATION_LANES):
        y = 6 - 2 * lane
        for x, ticker in zip(np.linspace(0, 3, len(tickers)), tickers):
            coordinates[ticker] = (x, y)
        fig.add_shape(
            type="rect", x0=-0.5, x1=3.5, y0=y - 0.7, y1=y + 0.7,
            fillcolor=c["lane_bg"], line=dict(color=c["lane_border"], width=1),
            layer="below", xref="x", yref="y",
        )
        fig.add_annotation(
            x=0, xref="paper", y=y + 0.85,
            text=f"<span style='text-transform:uppercase;letter-spacing:0.05em'>{label}</span>",
            showarrow=False, xanchor="left",
            font=dict(size=11, color=c["secondary"]),
        )

    evidence = rotation_evidence_table(snapshot)
    for (_, row), details in zip(snapshot.iterrows(), evidence.to_dict("records")):
        a, b = row["numerator"], row["denominator"]
        x0, y = coordinates[a]
        x1, _ = coordinates[b]
        valid = row["status"] == "Valid"
        directed = valid and pd.notna(row["leader"])
        is_selected = row["name"] == selected_pair
        color = c["accent"] if directed else c["neutral"]
        edge_width = 2.5 if is_selected else 1.5
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y, y], mode="lines", name=row["name"],
            line=dict(color=color, width=edge_width, dash="solid" if valid else "dot"),
            hoverinfo="skip", showlegend=False, meta="comparison",
        ))
        if directed:
            source_x, _ = coordinates[row["laggard"]]
            target_x, _ = coordinates[row["leader"]]
            fig.add_annotation(
                x=target_x, y=y, ax=source_x, ay=y,
                xref="x", yref="y", axref="x", ayref="y", text="",
                showarrow=True, arrowhead=3, arrowsize=1.5, arrowwidth=2.5,
                arrowcolor=color, standoff=14, startstandoff=14,
                name=row["name"],
            )
        label = _rotation_pct(row["ratio_change"]) if valid else "Unavailable"
        if valid and not directed:
            label = "Flat · 0.00%"
        pair_label = f"{e(row['numerator'])}/{e(row['denominator'])}"
        text = f"{pair_label}<br>{label}"
        fig.add_annotation(
            x=(x0 + x1) / 2, y=y + 0.22,
            text=f"<b>{text}</b>" if is_selected else text,
            showarrow=False, yanchor="bottom",
            font=dict(size=11, color=c["text"]),
            bordercolor=c["accent"] if is_selected else "rgba(0,0,0,0)",
            borderwidth=1 if is_selected else 0, borderpad=4,
            bgcolor=c["selected_glow"] if is_selected else "rgba(0,0,0,0)",
        )
        fields = list(details)
        hovertemplate = "<br>".join(
            f"{field}: %{{customdata[{i}]}}" for i, field in enumerate(fields)
        ) + "<extra></extra>"
        fig.add_trace(go.Scatter(
            x=np.linspace(x0, x1, 7)[1:-1], y=[y] * 5, mode="markers",
            marker=dict(size=24, color="rgba(0,0,0,0)"),
            customdata=[list(details.values())] * 5,
            hovertemplate=hovertemplate, name=row["name"], showlegend=False,
            meta="edge-hover",
        ))

    node_labels, node_hover = [], []
    for ticker in coordinates:
        matching = snapshot[(snapshot["numerator"] == ticker) | (snapshot["denominator"] == ticker)]
        row = matching.iloc[0] if not matching.empty else None
        leg = "numerator" if row is not None and row["numerator"] == ticker else "denominator"
        value = row[f"{leg}_return"] if row is not None else np.nan
        node_labels.append(f"<b>{e(ticker)}</b><br>{_rotation_pct(value)}")
        node_hover.append([
            e(ticker), CONFIG["ticker_legend"][ticker], _rotation_pct(value),
            _rotation_date(row["start_date"]) if row is not None else "Unavailable",
            _rotation_date(row["end_date"]) if row is not None else "Unavailable",
        ])
    fig.add_trace(go.Scatter(
        x=[p[0] for p in coordinates.values()], y=[p[1] for p in coordinates.values()],
        mode="markers+text", text=node_labels, textposition="bottom center",
        textfont=dict(color=c["text"], size=12),
        marker=dict(
            size=18, color=c["node_fill"],
            line=dict(color=c["node_ring"], width=2),
        ),
        customdata=node_hover, name="ETFs", meta="nodes", showlegend=False,
        hovertemplate=("%{customdata[0]} · %{customdata[1]}<br>Return: %{customdata[2]}"
                       "<br>%{customdata[3]} → %{customdata[4]}<extra></extra>"),
    ))
    for label, color, dash in [
        ("Arrow → stronger ETF", c["accent"], "solid"),
        ("Flat (no arrow)", c["neutral"], "solid"),
        ("Unavailable (no arrow)", c["neutral"], "dot"),
    ]:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="lines", name=label,
            line=dict(color=color, width=2, dash=dash), hoverinfo="skip",
        ))
    fig.update_layout(
        template=_PLOTLY_TEMPLATE, height=740,
        margin=dict(l=25, r=25, t=20, b=90),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["text"], family="Inter, sans-serif"),
        hoverlabel=dict(bgcolor=_DARK["slate"], font_size=13, font_family="Inter, sans-serif"),
        hovermode="closest", hoverdistance=24,
        xaxis=dict(range=[-0.6, 3.6], visible=False, fixedrange=True),
        yaxis=dict(range=[-0.8, 7.2], visible=False, fixedrange=True),
        legend=dict(
            orientation="h", x=0, y=-0.04,
            itemclick=False, itemdoubleclick=False,
            font=dict(color=c["secondary"]),
        ),
    )
    return fig

def build_heatmap(roc_df: pd.DataFrame) -> go.Figure:
    """Plotly heatmap of ROC values, red-to-green, centered at zero."""
    window_groups = {
        "1W": "Tactical",
        "1M": "Tactical",
        "3M": "Cyclical",
        "6M": "Cyclical",
        "1Y": "Structural",
        "2Y": "Structural",
        "5Y": "Structural",
    }

    cols = roc_df.columns.tolist()
    groups = [window_groups.get(c, "") for c in cols]

    dark_divergent = [
        [0.0, _DARK["red"]],
        [0.5, _DARK["slate"]],
        [1.0, _DARK["green"]],
    ]

    fig = go.Figure(
        go.Heatmap(
            z=roc_df.values,
            x=[groups, cols],
            y=roc_df.index.tolist(),
            colorscale=dark_divergent,
            zmid=0,
            xgap=2,
            ygap=2,
            text=roc_df.values,
            texttemplate="%{text:.1f}%",
            textfont=dict(size=13, color=_DARK["text"]),
            hovertemplate="Ticker: %{y}<br>Window: %{x}<br>ROC: %{z:.2f}%<extra></extra>",
        )
    )

    n_cols = len(cols)
    if n_cols > 1:
        prev_group = groups[0]
        for i in range(1, n_cols):
            if groups[i] != prev_group:
                fig.add_shape(
                    type="line",
                    x0=i / n_cols, x1=i / n_cols,
                    y0=0, y1=1,
                    xref="x domain", yref="y domain",
                    line=dict(color=_DARK["text"], width=2),
                )
                prev_group = groups[i]

    fig.update_layout(
        **_CHART_LAYOUT,
        height=max(320, 55 * len(roc_df)),
        margin=dict(l=60, r=20, t=40, b=30),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(side="top"),
    )
    return fig


def build_heatmap_echart(roc_df: pd.DataFrame) -> dict:
    """ECharts option spec for ROC heatmap."""

    cols = roc_df.columns.tolist()
    rows = [e(t) for t in roc_df.index]
    if not cols or not rows:
        return {
            "backgroundColor": "transparent",
            "title": {
                "text": "No heatmap data available",
                "left": "center",
                "top": "middle",
                "textStyle": {"color": _DARK["muted"], "fontSize": 14, "fontWeight": 400},
            },
            "xAxis": {"show": False},
            "yAxis": {"show": False},
            "series": [],
        }

    column_series: list[dict] = []
    min_val = np.inf
    max_val = -np.inf
    for x, window in enumerate(cols):
        column_points: list[dict] = []
        for y, _ticker in enumerate(rows):
            raw_value = roc_df.iat[y, x]
            if pd.notna(raw_value) and np.isfinite(raw_value):
                value = round(float(raw_value), 4)
                min_val = min(min_val, value)
                max_val = max(max_val, value)
                column_points.append({
                    "value": [x, y, value],
                    "label": {
                        "show": True,
                        "formatter": f"{value:.1f}%",
                        "fontSize": 11,
                        "color": _DARK["text"],
                    },
                })
            else:
                column_points.append({"value": [x, y, None], "label": {"show": False}})

        # Column-wise series with staggered delays gives a left-to-right cascade.
        column_series.append({
            "name": window,
            "type": "heatmap",
            "data": column_points,
            "itemStyle": {
                "borderColor": _ECHART_CELL_BORDER,
                "borderWidth": 1,
            },
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 8,
                    "shadowColor": _ECHART_SHADOW,
                }
            },
            "animationDuration": 700,
            "animationDelay": x * 120,
            "animationEasing": "cubicOut",
        })

    if not np.isfinite(min_val) or not np.isfinite(max_val):
        min_val, max_val = -1.0, 1.0

    bound = max(abs(min_val), abs(max_val), 1.0)

    option = {
        "backgroundColor": "transparent",
        "grid": {"left": "2%", "right": "1%", "top": "6%", "bottom": "18%", "containLabel": True},
        "tooltip": {
            "position": "top",
            "backgroundColor": _DARK["slate"],
            "borderColor": _ECHART_BORDER,
            "textStyle": {"color": _DARK["text"], "fontSize": 13},
        },
        "xAxis": {
            "type": "category",
            "position": "top",
            "data": cols,
            "axisTick": {"show": False},
            "axisLine": {"lineStyle": {"color": _ECHART_LINE}},
            "axisLabel": {
                "color": _DARK["muted"],
                "fontSize": 11,
                "lineHeight": 14,
                "margin": 12,
                "interval": 0,
            },
            "splitLine": {"show": False},
        },
        "yAxis": {
            "type": "category",
            "data": rows,
            "axisTick": {"show": False},
            "axisLine": {"lineStyle": {"color": _ECHART_LINE}},
            "axisLabel": {"color": _DARK["text"], "fontSize": 12, "margin": 6},
            "splitLine": {"show": False},
        },
        "visualMap": {
            "min": -bound,
            "max": bound,
            "calculable": False,
            "orient": "horizontal",
            "left": "center",
            "bottom": "3%",
            "itemWidth": 12,
            "itemHeight": 320,
            "precision": 1,
            "textStyle": {"color": _DARK["muted"], "fontSize": 11},
            "inRange": {"color": [_DARK["red"], _DARK["slate"], _DARK["green"]]},
        },
        "series": column_series,
    }
    return option


def build_ratio_chart(
    ratio: pd.Series,
    sma_dict: dict[str, pd.Series],
    pair_name: str,
) -> go.Figure:
    """Interactive line chart for a ratio pair with SMA overlays."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=ratio.index,
            y=ratio.values,
            mode="lines",
            name=pair_name,
            line=dict(color=_DARK["accent"], width=2),
            hovertemplate="<b>Date:</b> %{x|%b %d, %Y}<br><b>Ratio:</b> %{y:.4f}<extra></extra>",
        )
    )

    sma_styles = {
        50: dict(color=_DARK["amber"], width=1.5, dash="dash"),
        200: dict(color=_DARK["red"], width=1.5, dash="dot"),
    }

    for label, sma_series in sma_dict.items():
        length = int(label.split("-")[0])
        style = sma_styles.get(length, dict(color=_DARK["muted"], width=1, dash="dash"))
        fig.add_trace(
            go.Scatter(
                x=sma_series.index,
                y=sma_series.values,
                mode="lines",
                name=label,
                line=style,
            )
        )

    fig.update_layout(
        **_CHART_LAYOUT,
        title=dict(text=pair_name, font=dict(size=16, color=_DARK["text"]),
                   x=0.01, xanchor="left", yanchor="top"),
        height=390,
        margin=dict(l=40, r=20, t=60, b=30),
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="top", y=0.99, xanchor="right", x=0.99,
            bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=_DARK["muted"]),
        ),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=_DARK["grid"], zeroline=False),
    )
    fig.update_xaxes(rangeslider_visible=False)

    return fig


def build_ratio_echart(
    ratio: pd.Series,
    sma_dict: dict[str, pd.Series],
    pair_name: str,
) -> dict:
    """ECharts option spec for ratio chart with SMA overlays."""

    dates = [d.strftime("%Y-%m-%d") for d in ratio.index]

    series = [
        {
            "name": pair_name,
            "type": "line",
            "data": [round(float(v), 5) for v in ratio.values],
            "smooth": 0.3,
            "symbol": "none",
            "lineStyle": {"color": _DARK["accent"], "width": 2},
            "itemStyle": {"color": _DARK["accent"]},
            "animationDuration": 1500,
            "animationEasing": "cubicOut",
        }
    ]

    sma_colors = {50: _DARK["amber"], 200: _DARK["red"]}
    sma_dashes = {50: [6, 4], 200: [2, 4]}
    for i, (label, sma_series) in enumerate(sma_dict.items()):
        length = int(label.split("-")[0])
        aligned = sma_series.reindex(ratio.index)
        series.append({
            "name": label,
            "type": "line",
            "data": [round(float(v), 5) if pd.notna(v) else None for v in aligned.values],
            "smooth": 0.3,
            "symbol": "none",
            "lineStyle": {
                "color": sma_colors.get(length, _DARK["muted"]),
                "width": 1.5,
                "type": sma_dashes.get(length, [4, 4]),
            },
            "itemStyle": {"color": sma_colors.get(length, _DARK["muted"])},
            "animationDuration": 1800,
            "animationDelay": 300 + i * 200,
            "animationEasing": "cubicOut",
        })

    option = {
        "backgroundColor": "transparent",
        "title": {
            "text": pair_name,
            "left": "1%",
            "top": "2%",
            "textStyle": {"color": _DARK["text"], "fontSize": 16, "fontWeight": 500},
        },
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": _DARK["slate"],
            "borderColor": _ECHART_BORDER,
            "textStyle": {"color": _DARK["text"], "fontSize": 13},
        },
        "legend": {
            "data": [s["name"] for s in series],
            "orient": "horizontal",
            "left": "center",
            "bottom": "1%",
            "textStyle": {"color": _DARK["muted"], "fontSize": 11},
        },
        "grid": {"left": "4%", "right": "3%", "top": "18%", "bottom": "20%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": dates,
            "axisLine": {"lineStyle": {"color": _ECHART_LINE}},
            "axisLabel": {"color": _DARK["muted"], "fontSize": 11},
            "splitLine": {"show": False},
        },
        "yAxis": {
            "type": "value",
            "scale": True,
            "axisLine": {"show": False},
            "axisLabel": {"color": _DARK["muted"], "fontSize": 11},
            "splitLine": {"lineStyle": {"color": _DARK["grid"]}},
        },
        "series": series,
        "animationDuration": 1500,
        "animationEasing": "cubicOut",
    }

    return option


_ECHART_INVIEW = st.components.v2.component(
    "echart_inview",
    html="""
<div data-role="chart-slot" style="width:100%;height:100%;"></div>
""",
    js="""
const ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js";

function loadEcharts() {
    if (window.echarts) return Promise.resolve(window.echarts);
    if (window.__miniQuantEchartsPromise) return window.__miniQuantEchartsPromise;
    window.__miniQuantEchartsPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = ECHARTS_CDN;
        script.async = true;
        script.onload = () => resolve(window.echarts);
        script.onerror = () => reject(new Error("Failed to load ECharts"));
        document.head.appendChild(script);
    });
    return window.__miniQuantEchartsPromise;
}

const instances =
    window.__miniQuantEchartInViewInstances ||
    (window.__miniQuantEchartInViewInstances = new WeakMap());

export default function (component) {
    const parentElement = component.parentElement;
    const data = component.data || {};
    if (!parentElement) return;

    const height = Number(data.height || 390);
    const rawThreshold = Number(data.threshold);
    const threshold =
        Number.isFinite(rawThreshold) ? Math.max(0, Math.min(1, rawThreshold)) : 0.35;
    const option = data.option || null;
    const alt = data.alt || "Chart";

    let state = instances.get(parentElement);
    if (!state) {
        const root =
            parentElement.querySelector('[data-role="chart-slot"]') ||
            parentElement.firstElementChild ||
            parentElement;
        state = {
            root,
            chart: null,
            observer: null,
            mounted: false,
            latestOption: null,
            resizeHandler: null,
        };
        instances.set(parentElement, state);
    }

    if (!state.root) return;
    state.root.style.width = "100%";
    state.root.style.height = `${height}px`;
    state.root.setAttribute("role", "img");
    state.root.setAttribute("aria-label", alt);
    state.latestOption = option;

    function mountChart() {
        if (!state.latestOption) return;

        loadEcharts()
            .then((echarts) => {
                if (!echarts) return;

                if (!state.chart) {
                    state.chart = echarts.init(state.root, null, { renderer: "canvas" });
                    state.resizeHandler = () => {
                        if (state.chart) state.chart.resize();
                    };
                    window.addEventListener("resize", state.resizeHandler);
                }

                state.chart.clear();
                state.chart.setOption(state.latestOption, true);
                state.mounted = true;
            })
            .catch(() => {
                // Keep the slot quiet if CDN load fails.
            });
    }

    if (!state.mounted) {
        if (state.observer) state.observer.disconnect();
        state.observer = new IntersectionObserver(
            (entries, obs) => {
                const entry = entries[0];
                if (entry && entry.isIntersecting) {
                    obs.disconnect();
                    state.observer = null;
                    mountChart();
                }
            },
            { threshold }
        );
        state.observer.observe(state.root);
    } else {
        mountChart();
    }

    return () => {
        if (state.observer) {
            state.observer.disconnect();
            state.observer = null;
        }
        if (state.chart) {
            state.chart.dispose();
            state.chart = null;
        }
        if (state.resizeHandler) {
            window.removeEventListener("resize", state.resizeHandler);
            state.resizeHandler = null;
        }
        instances.delete(parentElement);
    };
}
""",
)


def render_echart_inview(
    option: dict,
    *,
    key: str,
    height: int = 390,
    threshold: float = 0.35,
    alt: str = "Chart",
) -> None:
    """Mount an ECharts chart only when its container enters the viewport."""
    _ECHART_INVIEW(
    key=key,
        data={"option": option, "height": height, "threshold": threshold, "alt": alt},
    width="stretch",
    height=height,
    )


def build_zscore_chart(
    zscore: pd.Series,
    thresholds: tuple[float, float],
    pair_name: str,
) -> go.Figure:
    """Bar chart of rolling Z-score with sigma-band overlays."""
    lo, hi = thresholds

    colors = [
        _DARK["red"] if v <= lo else _DARK["green"] if v >= hi else _ZSCORE_NEUTRAL_BAR
        for v in zscore.values
    ]

    fig = go.Figure(
        go.Bar(
            x=zscore.index,
            y=zscore.values,
            marker_color=colors,
            hovertemplate="Date: %{x|%Y-%m-%d}<br>Z-Score: %{y:.2f}<extra></extra>",
        )
    )

    y_max = max(abs(zscore.min()), abs(zscore.max()), 3.5) + 0.5
    fig.add_hrect(y0=-1, y1=1, fillcolor=_ZSCORE_BAND_NEUTRAL, line_width=0)
    fig.add_hrect(y0=1, y1=2, fillcolor=_ZSCORE_BAND_WARNING, line_width=0)
    fig.add_hrect(y0=-2, y1=-1, fillcolor=_ZSCORE_BAND_WARNING, line_width=0)
    fig.add_hrect(y0=2, y1=y_max, fillcolor=_ZSCORE_BAND_RISK, line_width=0)
    fig.add_hrect(y0=-y_max, y1=-2, fillcolor=_ZSCORE_BAND_RISK, line_width=0)

    fig.add_hline(y=hi, line_dash="dash", line_color=_DARK["green"], line_width=1,
                  annotation_text=f"+{hi}", annotation_position="top left",
                  annotation_font_color=_DARK["green"])
    fig.add_hline(y=lo, line_dash="dash", line_color=_DARK["red"], line_width=1,
                  annotation_text=str(lo), annotation_position="bottom left",
                  annotation_font_color=_DARK["red"])
    fig.add_hline(y=0, line_color=_DARK["muted"], line_width=0.5)

    fig.update_layout(
        **_CHART_LAYOUT,
        title=dict(text=f"{pair_name} — {CONFIG['zscore_window']}-Day Z-Score",
                   font=dict(size=16, color=_DARK["text"])),
        height=320,
        margin=dict(l=40, r=20, t=45, b=30),
        bargap=0,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
    )

    return fig


def build_zscore_echart(
    zscore: pd.Series,
    thresholds: tuple[float, float],
    pair_name: str,
) -> dict:
    """ECharts option spec for rolling Z-score bars."""

    lo, hi = thresholds
    dates = [d.strftime("%Y-%m-%d") for d in zscore.index]

    bars: list[dict] = []
    finite_values: list[float] = []
    for raw_value in zscore.values:
        if pd.notna(raw_value) and np.isfinite(raw_value):
            value = round(float(raw_value), 4)
            finite_values.append(abs(value))
            if value <= lo:
                color = _DARK["red"]
            elif value >= hi:
                color = _DARK["green"]
            else:
                color = _ZSCORE_NEUTRAL_BAR
            bars.append({"value": value, "itemStyle": {"color": color}})
        else:
            bars.append({"value": None, "itemStyle": {"color": _ZSCORE_NEUTRAL_BAR_FAINT}})

    y_max = max(finite_values) + 0.5 if finite_values else 4.0
    y_max = max(y_max, 4.0)

    option = {
        "backgroundColor": "transparent",
        "title": {
            "text": f"{pair_name} - {CONFIG['zscore_window']}-Day Z-Score",
            "left": "1%",
            "top": "2%",
            "textStyle": {"color": _DARK["text"], "fontSize": 16, "fontWeight": 500},
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": _DARK["slate"],
            "borderColor": _ECHART_BORDER,
            "textStyle": {"color": _DARK["text"], "fontSize": 13},
        },
        "grid": {"left": "4%", "right": "3%", "top": "20%", "bottom": "16%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": dates,
            "axisTick": {"show": False},
            "axisLine": {"lineStyle": {"color": _ECHART_LINE}},
            "axisLabel": {"color": _DARK["muted"], "fontSize": 11, "hideOverlap": True},
            "splitLine": {"show": False},
        },
        "yAxis": {
            "type": "value",
            "min": -y_max,
            "max": y_max,
            "axisLine": {"show": False},
            "axisLabel": {"color": _DARK["muted"], "fontSize": 11},
            "splitLine": {"show": False},
        },
        "series": [
            {
                "name": "Z-Score",
                "type": "bar",
                "data": bars,
                "barCategoryGap": "0%",
                "animationDuration": 1200,
                "animationEasing": "cubicOut",
                "markArea": {
                    "silent": True,
                    "data": [
                        [{"yAxis": -1, "itemStyle": {"color": _ZSCORE_BAND_NEUTRAL}}, {"yAxis": 1}],
                        [{"yAxis": 1, "itemStyle": {"color": _ZSCORE_BAND_WARNING}}, {"yAxis": 2}],
                        [{"yAxis": -2, "itemStyle": {"color": _ZSCORE_BAND_WARNING}}, {"yAxis": -1}],
                        [{"yAxis": 2, "itemStyle": {"color": _ZSCORE_BAND_RISK}}, {"yAxis": y_max}],
                        [{"yAxis": -y_max, "itemStyle": {"color": _ZSCORE_BAND_RISK}}, {"yAxis": -2}],
                    ],
                },
                "markLine": {
                    "silent": True,
                    "symbol": "none",
                    "lineStyle": {"width": 1},
                    "data": [
                        {
                            "yAxis": hi,
                            "lineStyle": {"type": "dashed", "color": _DARK["green"]},
                            "label": {
                                "show": True,
                                "formatter": f"+{hi:g}",
                                "color": _DARK["green"],
                                "position": "insideEndTop",
                                "distance": 6,
                            },
                        },
                        {
                            "yAxis": lo,
                            "lineStyle": {"type": "dashed", "color": _DARK["red"]},
                            "label": {
                                "show": True,
                                "formatter": f"{lo:g}",
                                "color": _DARK["red"],
                                "position": "insideEndBottom",
                                "distance": 6,
                            },
                        },
                        {
                            "yAxis": 0,
                            "lineStyle": {"type": "solid", "color": _DARK["muted"], "width": 0.5},
                            "label": {"show": False},
                        },
                    ],
                },
            }
        ],
    }

    return option


def build_financialization_echart(gap_df: pd.DataFrame) -> dict:
    """ECharts option spec for financialization grouped bars."""

    labels = gap_df["label"].tolist()
    gdp_vals = [round(float(v), 1) for v in gap_df["gdp_pct"]]
    mcap_vals = [round(float(v), 1) for v in gap_df["mcap_pct"]]

    option = {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": _DARK["slate"],
            "borderColor": _ECHART_BORDER,
            "textStyle": {"color": _DARK["text"], "fontSize": 13},
        },
        "legend": {
            "data": ["GDP Share (%)", "Market Cap Weight (%)"],
            "left": "0%",
            "top": "0%",
            "textStyle": {"color": _DARK["muted"], "fontSize": 11},
        },
        "grid": {"left": "8%", "right": "10%", "top": "12%", "bottom": "10%", "containLabel": True},
        "xAxis": {
            "type": "value",
            "name": "Share of Global Total (%)",
            "nameLocation": "middle",
            "nameGap": 30,
            "nameTextStyle": {"color": _DARK["muted"], "fontSize": 12},
            "axisLabel": {"color": _DARK["muted"], "fontSize": 11},
            "splitLine": {"lineStyle": {"color": _DARK["grid"]}},
            "axisLine": {"show": False},
        },
        "yAxis": {
            "type": "category",
            "data": labels,
            "inverse": True,
            "axisLabel": {"color": _DARK["text"], "fontSize": 12},
            "axisLine": {"lineStyle": {"color": _ECHART_LINE}},
            "splitLine": {"show": False},
        },
        "series": [
            {
                "name": "GDP Share (%)",
                "type": "bar",
                "data": gdp_vals,
                "itemStyle": {"color": _DARK["accent"], "borderRadius": [0, 3, 3, 0]},
                "label": {
                    "show": True, "position": "right",
                    "formatter": "{c}%",
                    "color": _DARK["text"], "fontSize": 11,
                },
                "animationDuration": 1200,
                "animationEasing": "cubicOut",
            },
            {
                "name": "Market Cap Weight (%)",
                "type": "bar",
                "data": mcap_vals,
                "itemStyle": {"color": _DARK["red"], "borderRadius": [0, 3, 3, 0]},
                "label": {
                    "show": True, "position": "right",
                    "formatter": "{c}%",
                    "color": _DARK["text"], "fontSize": 11,
                },
                "animationDuration": 1200,
                "animationDelay": 300,
                "animationEasing": "cubicOut",
            },
        ],
    }

    return option


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> dict:
    """Render sidebar controls and return a settings dict."""
    st.sidebar.title("Controls")

    lookback_label = st.sidebar.radio(
        "Lookback",
        list(LOOKBACK_MAP.keys()),
        index=1,
        horizontal=True,
        help="Date range for spread and Z-score charts.",
    )

    st.sidebar.markdown("#### Overlays")
    sma_50 = st.sidebar.checkbox(
        "50-day SMA", value=True,
        help="Simple Moving Average over 50 trading days (~2.5 months). Smooths short-term noise to show the medium-term trend direction.",
    )
    sma_200 = st.sidebar.checkbox(
        "200-day SMA", value=True,
        help="Simple Moving Average over 200 trading days (~10 months). The classic long-term trend line. Price crossing above or below it often signals a major regime shift.",
    )

    st.sidebar.markdown("---")

    with st.sidebar.expander("Ticker Legend", expanded=True):
        for ticker, desc in CONFIG["ticker_legend"].items():
            st.markdown(f"**{e(ticker)}** — {desc}")

    st.sidebar.markdown("---")
    st.sidebar.caption("Cached 12 h · Yahoo Finance")

    return {
        "lookback_label": lookback_label,
        "lookback_days": LOOKBACK_MAP[lookback_label],
        "sma_50_enabled": sma_50,
        "sma_200_enabled": sma_200,
    }


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------

ANALYSIS_DIR = Path(__file__).parent / "analysis"


def _pair_name_to_slug(pair_name: str) -> str:
    """'SPY / RSP' -> 'spy-rsp'"""
    return pair_name.lower().replace(" / ", "-").replace("/", "-")


def get_latest_analysis(report_type: str) -> str | None:
    """Find the latest analysis file of a given type and return its content.

    report_type is the suffix after YYYY-MM-, e.g. 'macro', 'snapshot',
    'trend', or a pair slug like 'spy-rsp'.
    """
    if not ANALYSIS_DIR.exists():
        return None
    matches = sorted(ANALYSIS_DIR.glob(f"*-{report_type}.md"), reverse=True)
    if not matches:
        return None
    return matches[0].read_text()


def render_analysis_tab():
    """Render the Analysis tab — shows the latest macro report."""
    content = get_latest_analysis("macro")
    if content:
        st.markdown(content)
    else:
        st.info(
            "No macro report yet. Run `/analyze-macro` in Claude Code "
            "to generate your first monthly report."
        )


def render_rotation_tab(prices: pd.DataFrame):
    """Connect existing pair signals without implying observed capital transfers."""
    st.header("Capital Rotation Network")
    st.caption(
        "Arrows indicate relative outperformance direction, not measured fund flows. "
        "The stronger ETF may still have fallen in absolute terms. "
        "USD-adjusted prices include currency effects."
    )
    st.caption(
        "🔧 *Structural awareness lens — maps which ETFs are mechanically outperforming "
        "within each comparison lane over the selected window.*"
    )
    if prices.empty:
        st.warning(NO_DATA_MSG)
        return

    prices = prices.sort_index()
    if prices.index.has_duplicates:
        st.error("Duplicate market-data dates prevent a shared-date rotation comparison.")
        return
    windows = {label: n for label, n, _ in CONFIG["roc_windows"]
               if n <= 252 and len(prices) >= n + 1}
    if not windows:
        st.info("At least six price observations are needed for a one-week comparison.")
        return

    window_col, pair_col = st.columns([1, 2])
    with window_col:
        labels = list(windows)
        window = st.selectbox(
            "Rotation window", labels, index=labels.index("1M") if "1M" in labels else 0,
            key="rotation_window", help="Approximate trading-session intervals, not calendar periods.",
        )
    with pair_col:
        pair_options = {pair_display_name(p): p["name"] for p in CONFIG["ratio_pairs"]}
        selected_display = st.selectbox(
            "Inspect comparison", list(pair_options),
            index=2, key="rotation_pair",
        )
        selected_pair = pair_options[selected_display]

    n_sessions = windows[window]
    snapshot = calc_rotation_table(prices, n_sessions)
    current_start, as_of = snapshot.iloc[0][["start_date", "end_date"]]
    age = max(0, (pd.Timestamp.now().normalize() - pd.Timestamp(as_of).normalize()).days)
    valid_count = int((snapshot["status"] == "Valid").sum())
    st.caption(
        f"{_rotation_date(current_start)} → {_rotation_date(as_of)} · "
        f"{n_sessions} observed trading-session intervals · "
        f"{valid_count}/{len(snapshot)} valid comparisons · "
        f"Data age: {age} calendar days · Yahoo Finance, cached for 12 hours"
    )
    if age > 7:
        st.warning(
            "The latest shared price date is over seven calendar days old. "
            "This is a calendar-age heuristic, not an exchange-session freshness check."
        )
    if valid_count < len(snapshot):
        st.warning("Some comparisons are unavailable. No directional arrow is drawn for them; hover over a link for data-quality details.")
    st.plotly_chart(
        build_rotation_network(snapshot, selected_pair),
        width="stretch", theme=None, key="rotation_network",
        config={"displayModeBar": False},
    )
    st.caption(
        "Labels = signed ratio changes. Arrow/node sizes are not proportional to capital. "
        "Highlighted label = selected comparison."
    )

    selected = snapshot.loc[snapshot["name"] == selected_pair].iloc[0]
    st.markdown(
        f"**{selected_display}: {_rotation_direction(selected)}** · "
        f"Ratio change: {_rotation_pct(selected['ratio_change'])} · {selected['transition']}"
    )
    if selected["previous_status"] != "Valid":
        st.caption(f"Prior comparison: {selected['previous_status']}")
    with st.expander(f"{selected_display} — ratio history", expanded=False):
        pair_tickers = [selected["numerator"], selected["denominator"]]
        if any(t not in prices.columns for t in pair_tickers):
            st.info("Both ETF price series are needed for this history.")
            return
        history_start = selected["previous_start_date"]
        if pd.isna(history_start):
            history_start = selected["start_date"]
            st.caption("Only the current window is shown; a full preceding window is unavailable.")
        history_prices = prices.loc[history_start:as_of, pair_tickers]
        clean_prices = history_prices.where(np.isfinite(history_prices) & (history_prices > 0))
        ratio = calc_ratio(clean_prices, *pair_tickers).reindex(history_prices.index)
        if not ratio.notna().any():
            st.info("No valid paired observations are available for this history.")
            return
        fig = build_ratio_chart(ratio, {}, selected_display)
        fig.update_traces(connectgaps=False)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(
            rangeslider_visible=False, showspikes=True, spikemode="across",
            spikesnap="cursor", spikethickness=1, spikecolor=_ROTATION["neutral"],
        )
        fig.add_vline(x=pd.Timestamp(current_start).to_pydatetime(), line_width=1, line_color=_ROTATION["neutral"])
        st.plotly_chart(fig, width="stretch", theme=None, key="rotation_history")
        st.caption(
            f"Current window: {_rotation_date(current_start)} → {_rotation_date(as_of)}. "
            "The vertical line marks its start; earlier observations are prior-window context. "
            "Gaps are not filled."
        )
        st.dataframe(
            ratio.rename("Ratio").rename_axis("Date").reset_index(),
            width="stretch", hide_index=True,
        )


def render_dashboard_tab(settings: dict, prices: pd.DataFrame):
    """Render the Dashboard tab — all charts and data."""
    if prices.empty:
        st.warning(NO_DATA_MSG)
        return

    # --- Section A: Momentum Heatmap ----------------------------------------
    st.header("What's Moving")
    st.caption(
        "Rate-of-change across tactical (1W–1M), cyclical (3M–6M), and structural "
        "(1Y–5Y) horizons. Green = positive adjusted-price return, red = negative. "
        "These are price changes, not fund flows."
    )
    st.caption(
        "🔧 *Structural awareness lens — identifies where systematic engines "
        "(passive inflows, CTA trend-following, VaR triggers) are forcing capital "
        "across time horizons.*"
    )

    heatmap_tickers = [t for t in CONFIG["heatmap_tickers"] if t in prices.columns]
    heatmap_prices = prices[heatmap_tickers]

    active_roc_windows = [
        w for w in CONFIG["roc_windows"]
        if w[2] <= settings["lookback_days"]
    ]

    roc_df = calc_roc_table(heatmap_prices, active_roc_windows)
    st.caption("Horizon buckets: Tactical (1W-1M) | Cyclical (3M-6M) | Structural (1Y-5Y)")
    heatmap_height = max(320, 42 * len(roc_df))
    st.echarts_chart(
        build_heatmap_echart(roc_df),
        width="stretch",
        height=heatmap_height,
        theme=None,
        key="signal-heatmap-echart",
        alt="Momentum heatmap of ticker returns across tactical, cyclical, and structural horizons.",
    )

    # --- Per-pair drill-down: spread + Z-score --------------------------------
    st.header("Where Is Leadership Shifting")
    st.caption(
        "Ratio spread with SMA overlays and rolling Z-score per pair. A rising ratio means "
        "the numerator is outperforming. Z-score values beyond +/-2 sigma flag positions that "
        "are statistically crowded or stretched relative to recent history."
    )
    st.caption(
        "🛡️ *Self-defense lens — ratio extremes and Z-score crowding help identify "
        "value traps (structurally cheap for a reason) and crowded trades "
        "(passive concentration at historical extremes).*"
    )

    cutoff = pd.Timestamp.now() - pd.Timedelta(days=settings["lookback_days"])

    for pair in CONFIG["ratio_pairs"]:
        pair_name = pair["name"]
        display_name = pair_display_name(pair)
        if pair["numerator"] not in prices.columns or pair["denominator"] not in prices.columns:
            st.info(f"Price data unavailable for {display_name}.")
            continue

        with st.container(border=True):
            ratio = calc_ratio(prices, pair["numerator"], pair["denominator"])

            sma_dict: dict[str, pd.Series] = {}
            for length in CONFIG["sma_lengths"]:
                if (length == 50 and settings["sma_50_enabled"]) or (
                    length == 200 and settings["sma_200_enabled"]
                ):
                    sma_dict[f"{length}-SMA"] = calc_sma(ratio, length)

            ratio_display = ratio.loc[ratio.index >= cutoff]
            sma_display = {k: v.loc[v.index >= cutoff] for k, v in sma_dict.items()}

            render_echart_inview(
                build_ratio_echart(ratio_display, sma_display, display_name),
                key=f"ratio-echart-{_pair_name_to_slug(pair_name)}",
                height=390,
                threshold=0.7,
                alt=f"{display_name} ratio spread chart with SMA overlays.",
            )

            zscore = calc_zscore(ratio, CONFIG["zscore_window"])
            zscore_display = zscore.loc[zscore.index >= cutoff]
            render_echart_inview(
                build_zscore_echart(zscore_display, CONFIG["zscore_thresholds"], display_name),
                key=f"zscore-echart-{_pair_name_to_slug(pair_name)}",
                height=340,
                threshold=0.35,
                alt=f"{display_name} rolling z-score bars with sigma bands.",
            )

            st.caption(pair["tooltip"])

            chart_md = get_latest_analysis(_pair_name_to_slug(pair_name))
            if chart_md:
                with st.expander(f"{display_name} — Analysis", expanded=False):
                    st.markdown(chart_md)

    # --- Section D: Physical & Cash-Flow Anchoring -----------------------------
    st.header("Is It Justified")
    st.caption(
        "Compares each region's share of global market capitalization against its share of global GDP. "
        "A large positive gap indicates capital markets are pricing significantly beyond real economic "
        "output — a structural crowding signal."
    )
    st.caption(
        "⚓ *Physical anchoring lens — compares financialized valuations against hard "
        "economic controls that cannot be inflated by passive flows or index-rule mechanics.*"
    )

    gap_df = calc_financialization_gap(MACRO_ANCHORS["regions"])
    financialization_height = max(300, 80 * len(gap_df))
    render_echart_inview(
        build_financialization_echart(gap_df),
        key="financialization-gap-echart",
        height=financialization_height,
        threshold=0.2,
        alt="Regional GDP share and market-cap weight comparison chart.",
    )

    gap_display = gap_df[["label", "gdp_pct", "mcap_pct", "gap_pct"]].copy()
    gap_display.columns = ["Region", "GDP Share %", "Mkt Cap Weight %", "Gap (pp)"]
    st.dataframe(
        gap_display.style.format(
            {"GDP Share %": "{:.1f}", "Mkt Cap Weight %": "{:.1f}", "Gap (pp)": "{:+.1f}"}
        ),
        width="stretch",
        hide_index=True,
    )

    vintage = MACRO_ANCHORS["last_updated"]
    vintage_text = f"Data vintage: {vintage}" if vintage[0].isdigit() else "Vintage: update MACRO_ANCHORS in settings/market.py"
    st.caption(
        f"{vintage_text} · "
        f"GDP: {MACRO_ANCHORS['gdp_source']} · "
        f"Mkt Cap: {MACRO_ANCHORS['mcap_source']}"
    )



def main():
    settings = render_sidebar()

    st.title("Capital Structure Decoder")
    st.caption(
        "Financial headlines are post-hoc rationalizations. These charts decode what actually "
        "moves capital: systematic VaR triggers, passive index weightings, options gamma, and "
        "401(k) inflow flywheels. By tracking ratio spreads, rolling Z-score extremes, and "
        "physical anchors like FCF yield and energy output against financialized price, the "
        "goal is simple — see where structural engines are forced to pump or dump capital, "
        "and avoid standing on the wrong side of the tide."
    )

    all_tickers = tuple(get_all_tickers())
    sma_buffer = max(CONFIG["sma_lengths"]) + 10
    fetch_days = settings["lookback_days"] + sma_buffer + 60
    try:
        prices = fetch_data(all_tickers, fetch_days)
    except Exception as exc:
        st.warning(f"Market-data download issue: {exc}")
        prices = pd.DataFrame()

    tab_dashboard, tab_analysis = st.tabs(["Signal", "Analysis"])

    with tab_dashboard:
        render_dashboard_tab(settings, prices)

    with tab_analysis:
        render_analysis_tab()



if __name__ == "__main__":
    main()
