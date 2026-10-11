from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core import (
    calc_financialization_gap,
    calc_ratio,
    calc_roc_table,
    calc_sma,
    calc_zscore,
    pair_display_name,
)
from settings.app_constants import NO_DATA_MSG
from settings.market import CONFIG, MACRO_ANCHORS
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

ANALYSIS_DIR = Path(__file__).resolve().parent.parent / "analysis"


def _pair_name_to_slug(pair_name: str) -> str:
    return pair_name.lower().replace(" / ", "-").replace("/", "-")


def get_latest_analysis(report_type: str) -> str | None:
    if not ANALYSIS_DIR.exists():
        return None
    matches = sorted(ANALYSIS_DIR.glob(f"*-{report_type}.md"), reverse=True)
    if not matches:
        return None
    return matches[0].read_text()


def render_signal_tab(
    settings: dict,
    prices: pd.DataFrame,
    *,
    theme_mode: str = "dark",
) -> None:
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
        "Structural awareness: where are systematic engines "
        "(passive inflows, CTA trend-following, VaR triggers) forcing capital "
        "across time horizons?"
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
        build_heatmap_echart(roc_df, theme_mode=theme_mode),
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
        "the numerator is outperforming. Z-scores beyond +/-2 sigma flag crowded or "
        "stretched positions relative to recent history."
    )
    st.caption(
        "Self-defense: ratio extremes and Z-score crowding help spot "
        "value traps (structurally cheap for a reason) and crowded trades "
        "(passive concentration at historical extremes)."
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
                build_ratio_echart(ratio_display, sma_display, display_name, theme_mode=theme_mode),
                key=f"ratio-echart-{_pair_name_to_slug(pair_name)}",
                height=390,
                threshold=0.7,
                alt=f"{display_name} ratio spread chart with SMA overlays.",
            )

            zscore = calc_zscore(ratio, CONFIG["zscore_window"])
            zscore_display = zscore.loc[zscore.index >= cutoff]
            render_echart_inview(
                build_zscore_echart(zscore_display, CONFIG["zscore_thresholds"], display_name, theme_mode=theme_mode),
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
        "Compares each region's share of global market cap against its share of global GDP. "
        "A large positive gap means capital markets are pricing well beyond real economic "
        "output, a structural crowding signal."
    )
    st.caption(
        "Physical anchoring: financialized valuations vs. hard economic controls "
        "that passive flows and index-rule mechanics can't inflate."
    )

    gap_df = calc_financialization_gap(MACRO_ANCHORS["regions"])
    financialization_height = max(300, 80 * len(gap_df))
    render_echart_inview(
        build_financialization_echart(gap_df, theme_mode=theme_mode),
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

    # --- Section E: AI Capex Loop (seasonal) ----------------------------------
    ctx_mag7 = load_context("mag7-circular-revenue")
    if ctx_mag7:
        st.header("The AI Capex Loop")
        st.caption(
            f"\U0001f504 *{ctx_mag7['context_type']}* · Data as of {ctx_mag7['data_as_of']} · "
            f"Refreshed every ~{ctx_mag7['freshness_days']} days."
        )
        _d = ctx_mag7["data"]
        _n_buyers = len(_d.get("capex_by_company", {}))
        st.caption(
            f"Tracks how ${_d['hyperscaler_ai_capex_annual_bn']:.0f}B/yr in hyperscaler AI capex "
            f"circulates within the Mag 7. NVDA receives {_d['nvidia_dc_rev_hyperscaler_pct']:.0f}% "
            f"of its datacenter revenue from {_n_buyers} hyperscaler buyers. "
            "Revenue that arrives as a peer's capex is not new end-user demand."
        )

        with st.container(border=True):
            render_echart_inview(
                build_sankey_echart(ctx_mag7, theme_mode=theme_mode),
                key="context-sankey-mag7",
                height=400,
                threshold=0.2,
                alt="Sankey diagram showing circular AI capex flows between Mag 7 members.",
            )

        d = ctx_mag7["data"]
        intercompany_bn = round(d["mag7_total_rev_ttm_bn"] * d["mag7_intercompany_rev_pct"] / 100)
        c1, c2, c3 = st.columns(3)
        c1.metric("Revenue Between Members", f"~${intercompany_bn}B/yr")
        c1.caption(f"{d['mag7_intercompany_rev_pct']}% of Mag 7 combined revenue")
        c2.metric("Hyperscaler AI Capex", f"${d['hyperscaler_ai_capex_annual_bn']:.0f}B/yr")
        c2.caption(f"{len(d.get('capex_by_company', {}))} companies spending on AI infrastructure")
        c3.metric("NVDA Revenue from Buyers", f"{d['nvidia_dc_rev_hyperscaler_pct']:.0f}%")
        c3.caption("of NVIDIA datacenter revenue from these same hyperscalers")

        st.caption(
            f"Sources: {', '.join(ctx_mag7['sources'][:3])}."
        )

    # --- Section F: Physical vs Financial Weight (structural) ------------------
    ctx_physical = load_context("physical-anchors")
    if ctx_physical:
        st.header("Physical vs Financial Weight")
        st.caption(
            f"⚓ *{ctx_physical['context_type']}* · Data as of {ctx_physical['data_as_of']} · "
            f"Refreshed every ~{ctx_physical['freshness_days']} days."
        )
        st.caption(
            "Each region's share of physical output (energy, manufacturing) vs. its share of "
            "global equity market cap. A large gap between physical and financial weight "
            "is a financialization premium or discount."
        )

        with st.container(border=True):
            render_echart_inview(
                build_butterfly_echart(ctx_physical["data"], MACRO_ANCHORS["regions"], theme_mode=theme_mode),
                key="context-butterfly-physical",
                height=340,
                threshold=0.2,
                alt="Butterfly chart comparing physical economy share vs market cap weight.",
            )

        us_energy = ctx_physical["data"]["us_energy_pct"]
        us_mfg = ctx_physical["data"]["us_manufacturing_pct"]
        cn_energy = ctx_physical["data"]["china_energy_pct"]
        cn_mfg = ctx_physical["data"]["china_manufacturing_pct"]
        us_mcap = next((r["mcap_pct"] for r in MACRO_ANCHORS["regions"] if r["label"] == "US"), 0)
        cn_mcap = next((r["mcap_pct"] for r in MACRO_ANCHORS["regions"] if r["label"] == "China"), 0)

        st.markdown(
            f"| | Energy | Manufacturing | Market Cap | Financial / Physical |\n"
            f"|---|---|---|---|---|\n"
            f"| **US** | {us_energy}% | {us_mfg}% | {us_mcap}% | ~{us_mcap / ((us_energy + us_mfg) / 2):.0f}x |\n"
            f"| **China** | {cn_energy}% | {cn_mfg}% | {cn_mcap}% | ~{cn_mcap / ((cn_energy + cn_mfg) / 2):.1f}x |\n"
            f"| **Ratio** | | | **~{(us_mcap / ((us_energy + us_mfg) / 2)) / (cn_mcap / ((cn_energy + cn_mfg) / 2)):.0f}:1** | |"
        )

        st.caption(
            f"Sources: {', '.join(ctx_physical['sources'])}. "
            f"Energy data: {ctx_physical['data']['data_year_energy']}. "
            f"Manufacturing data: {ctx_physical['data']['data_year_manufacturing']}."
        )

    # --- Section G: Systematic Positioning (tactical) -------------------------
    ctx_positioning = load_context("systematic-positioning")
    if ctx_positioning:
        st.header("Systematic Positioning")
        st.caption(
            f"\U0001f3af *{ctx_positioning['context_type']}* · Data as of {ctx_positioning['data_as_of']} · "
            f"Refreshed every ~{ctx_positioning['freshness_days']} days."
        )
        st.caption(
            "Three autopilot strategies that collectively move billions (trend-followers, "
            "options dealers, volatility-based allocators) are all betting the same "
            "direction: long US stocks. None of them care about valuation. They react "
            "to price momentum, volatility, and capital flows."
        )

        with st.container(border=True):
            render_echart_inview(
                build_gauges_echart(ctx_positioning, theme_mode=theme_mode),
                key="context-gauges-positioning",
                height=280,
                threshold=0.2,
                alt="Triple gauge showing CTA positioning, dealer gamma, and vol-target allocation.",
            )

        st.caption(
            f"{ctx_positioning['data']['notes']}"
        )
        st.caption(
            f"Sources: {', '.join(ctx_positioning['sources'])}."
        )

    from ui.navigation import render_back_to_top
    render_back_to_top(theme_mode, key="signal-back-to-top")
