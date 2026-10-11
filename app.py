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
from datetime import datetime, timedelta
from pathlib import Path
from settings.market import CONFIG, LOOKBACK_MAP
from core import e, get_all_tickers
import ui.theme as theme_utils
import ui.navigation as nav_utils
import ui.opinion_tab as opinion_tab
import ui.signal_tab as signal_tab
from ui.charts import (
    build_butterfly_echart,
    build_financialization_echart,
    build_gauges_echart,
    build_heatmap_echart,
    build_ratio_echart,
    build_sankey_echart,
    build_zscore_echart,
    load_context,
)
from ui.echart_component import render_echart_inview


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
theme_utils.inject_theme_styles(_THEME_MODE)


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=43200, show_spinner="Fetching market data…")
def fetch_data(tickers: tuple[str, ...], period_days: int) -> pd.DataFrame:
    """Download adjusted-close prices for all tickers via yfinance."""
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

    if isinstance(df.columns, pd.MultiIndex):
        df = df["Close"]
    else:
        df = df[["Close"]].rename(columns={"Close": tickers[0]})

    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    return df


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar(theme_mode: str) -> dict:
    st.sidebar.title("Situationally Aware")
    with st.sidebar:
        nav_utils.render_toc(theme_mode)
    st.sidebar.markdown("---")

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
# Main
# ---------------------------------------------------------------------------

def main():
    settings = render_sidebar(_THEME_MODE)

    st.title("Capital Structure Decoder")
    st.caption(
        "Financial headlines are post-hoc rationalizations. What actually moves capital: "
        "VaR triggers, passive index weightings, options gamma, 401(k) inflow flywheels. "
        "These charts track ratio spreads, Z-score extremes, and physical anchors (FCF yield, "
        "energy output) against financialized price. The point is to see where structural "
        "engines are forced to pump or dump capital, and avoid standing on the wrong side."
    )

    all_tickers = tuple(get_all_tickers())
    sma_buffer = max(CONFIG["sma_lengths"]) + 10
    fetch_days = settings["lookback_days"] + sma_buffer + 60
    try:
        prices = fetch_data(all_tickers, fetch_days)
    except Exception as exc:
        st.warning(f"Market-data download issue: {exc}")
        prices = pd.DataFrame()

    tab_signal, tab_opinion = st.tabs(["Signal", "Opinion"])

    with tab_signal:
        signal_tab.render_signal_tab(settings, prices, theme_mode=_THEME_MODE)

    with tab_opinion:
        _chart_builders = {
            "build_ratio_echart": build_ratio_echart,
            "build_zscore_echart": build_zscore_echart,
            "build_heatmap_echart": build_heatmap_echart,
            "build_financialization_echart": build_financialization_echart,
            "build_gauges_echart": build_gauges_echart,
            "build_sankey_echart": build_sankey_echart,
            "build_butterfly_echart": build_butterfly_echart,
            "load_context": load_context,
        }
        opinion_tab.render_opinion_tab(
            settings,
            prices,
            theme_mode=_THEME_MODE,
            render_echart=render_echart_inview,
            chart_builders=_chart_builders,
        )


if __name__ == "__main__":
    main()
