"""Extract all dashboard metrics as JSON for analysis skills.

Usage:
    python scripts/extract_data.py            # JSON to stdout
    python scripts/extract_data.py -o out.json # JSON to file
"""

import json
import sys
import os
import argparse
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import (
    CONFIG,
    MACRO_ANCHORS,
    FUNDAMENTALS_TICKERS,
    get_all_tickers,
    calc_roc_table,
    calc_ratio,
    calc_sma,
    calc_zscore,
    calc_financialization_gap,
)

TREND_MONTHS = 6
FETCH_DAYS = 730 + 260


def fetch_prices(tickers: list[str], days: int) -> pd.DataFrame:
    end = datetime.now()
    start = end - timedelta(days=days)

    df = yf.download(
        tickers,
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


def safe_float(val) -> float | None:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return round(float(val), 6)


def extract_heatmap(prices: pd.DataFrame) -> dict:
    heatmap_tickers = [t for t in CONFIG["heatmap_tickers"] if t in prices.columns]
    roc_windows = [w for w in CONFIG["roc_windows"] if w[2] <= 365]
    roc_df = calc_roc_table(prices[heatmap_tickers], roc_windows)

    result = {}
    for ticker in roc_df.index:
        result[ticker] = {
            col: safe_float(roc_df.loc[ticker, col])
            for col in roc_df.columns
        }
    return result


def extract_ratio_pair(prices: pd.DataFrame, pair: dict) -> dict:
    ratio = calc_ratio(prices, pair["numerator"], pair["denominator"])

    sma_50 = calc_sma(ratio, 50)
    sma_200 = calc_sma(ratio, 200)

    cutoff = pd.Timestamp.now() - pd.Timedelta(days=TREND_MONTHS * 30)
    ratio_6m = ratio.loc[ratio.index >= cutoff]

    current = safe_float(ratio.iloc[-1]) if len(ratio) > 0 else None
    sma_50_val = safe_float(sma_50.iloc[-1]) if len(sma_50) > 0 else None
    sma_200_val = safe_float(sma_200.iloc[-1]) if len(sma_200) > 0 else None

    value_6m_ago = safe_float(ratio_6m.iloc[0]) if len(ratio_6m) > 0 else None
    change_6m_pct = None
    if current is not None and value_6m_ago is not None and value_6m_ago != 0:
        change_6m_pct = round((current / value_6m_ago - 1) * 100, 2)

    high_6m = safe_float(ratio_6m.max()) if len(ratio_6m) > 0 else None
    low_6m = safe_float(ratio_6m.min()) if len(ratio_6m) > 0 else None

    percentile_6m = None
    if len(ratio_6m) > 1 and current is not None:
        percentile_6m = round(float((ratio_6m <= current).sum() / len(ratio_6m) * 100), 1)

    monthly_values = []
    if len(ratio_6m) > 0:
        monthly = ratio_6m.resample("ME").last().dropna()
        for date, val in monthly.items():
            monthly_values.append({
                "date": date.strftime("%Y-%m"),
                "value": safe_float(val),
            })

    position_vs_sma50 = None
    if current is not None and sma_50_val is not None:
        position_vs_sma50 = "above" if current > sma_50_val else "below"

    position_vs_sma200 = None
    if current is not None and sma_200_val is not None:
        position_vs_sma200 = "above" if current > sma_200_val else "below"

    sma50_above_sma200 = None
    if sma_50_val is not None and sma_200_val is not None:
        sma50_above_sma200 = sma_50_val > sma_200_val

    return {
        "name": pair["name"],
        "numerator": pair["numerator"],
        "denominator": pair["denominator"],
        "tooltip": pair["tooltip"],
        "current": current,
        "sma_50": sma_50_val,
        "sma_200": sma_200_val,
        "position_vs_sma50": position_vs_sma50,
        "position_vs_sma200": position_vs_sma200,
        "sma50_above_sma200": sma50_above_sma200,
        "value_6m_ago": value_6m_ago,
        "change_6m_pct": change_6m_pct,
        "high_6m": high_6m,
        "low_6m": low_6m,
        "percentile_6m": percentile_6m,
        "monthly_values": monthly_values,
    }


def extract_zscore(prices: pd.DataFrame, pair: dict) -> dict:
    ratio = calc_ratio(prices, pair["numerator"], pair["denominator"])
    zscore = calc_zscore(ratio, CONFIG["zscore_window"])

    cutoff = pd.Timestamp.now() - pd.Timedelta(days=TREND_MONTHS * 30)
    zscore_6m = zscore.loc[zscore.index >= cutoff]

    current = safe_float(zscore.iloc[-1]) if len(zscore) > 0 else None
    high_6m = safe_float(zscore_6m.max()) if len(zscore_6m) > 0 else None
    low_6m = safe_float(zscore_6m.min()) if len(zscore_6m) > 0 else None

    lo, hi = CONFIG["zscore_thresholds"]
    days_above = int((zscore_6m >= hi).sum()) if len(zscore_6m) > 0 else 0
    days_below = int((zscore_6m <= lo).sum()) if len(zscore_6m) > 0 else 0

    direction = None
    if len(zscore_6m) >= 21:
        recent_mean = zscore_6m.iloc[-21:].mean()
        older_mean = zscore_6m.iloc[:21].mean()
        diff = recent_mean - older_mean
        if diff > 0.3:
            direction = "rising"
        elif diff < -0.3:
            direction = "falling"
        else:
            direction = "sideways"

    return {
        "pair_name": pair["name"],
        "window": CONFIG["zscore_window"],
        "thresholds": list(CONFIG["zscore_thresholds"]),
        "current": current,
        "high_6m": high_6m,
        "low_6m": low_6m,
        "days_above_upper": days_above,
        "days_below_lower": days_below,
        "direction": direction,
    }


def extract_financialization() -> dict:
    gap_df = calc_financialization_gap(MACRO_ANCHORS["regions"])
    regions = []
    for _, row in gap_df.iterrows():
        regions.append({
            "label": row["label"],
            "etf": row["etf"],
            "gdp_pct": row["gdp_pct"],
            "mcap_pct": row["mcap_pct"],
            "gap_pct": round(row["gap_pct"], 1),
        })
    return {
        "last_updated": MACRO_ANCHORS["last_updated"],
        "gdp_source": MACRO_ANCHORS["gdp_source"],
        "mcap_source": MACRO_ANCHORS["mcap_source"],
        "regions": regions,
    }


def extract_fundamentals(tickers: list[str]) -> dict:
    stocks = []
    total_mcap = 0
    weighted_fcf = 0
    fcf_yields = []

    for symbol in tickers:
        try:
            info = yf.Ticker(symbol).info
        except Exception:
            stocks.append({
                "symbol": symbol,
                "market_cap": None,
                "free_cashflow": None,
                "fcf_yield_pct": None,
                "trailing_pe": None,
                "forward_pe": None,
                "error": "failed to fetch",
            })
            continue

        mcap = info.get("marketCap")
        fcf = info.get("freeCashflow")
        trailing_pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")

        fcf_yield_pct = None
        if mcap and fcf and mcap > 0:
            fcf_yield_pct = round(fcf / mcap * 100, 2)
            fcf_yields.append(fcf_yield_pct)
            total_mcap += mcap
            weighted_fcf += fcf

        stocks.append({
            "symbol": symbol,
            "market_cap": mcap,
            "free_cashflow": fcf,
            "fcf_yield_pct": fcf_yield_pct,
            "trailing_pe": safe_float(trailing_pe) if trailing_pe else None,
            "forward_pe": safe_float(forward_pe) if forward_pe else None,
        })

    simple_avg = round(sum(fcf_yields) / len(fcf_yields), 2) if fcf_yields else None
    mcap_weighted = round(weighted_fcf / total_mcap * 100, 2) if total_mcap > 0 else None

    return {
        "tickers": tickers,
        "stocks": stocks,
        "aggregates": {
            "simple_avg_fcf_yield_pct": simple_avg,
            "mcap_weighted_fcf_yield_pct": mcap_weighted,
            "stocks_with_data": len(fcf_yields),
            "stocks_total": len(tickers),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Extract dashboard metrics as JSON")
    parser.add_argument("-o", "--output", help="Write JSON to file instead of stdout")
    parser.add_argument("--archive", action="store_true",
                        help="Also save a copy to analysis/YYYY-MM-data.json")
    args = parser.parse_args()

    print("Fetching price data...", file=sys.stderr)
    tickers = get_all_tickers()
    prices = fetch_prices(tickers, FETCH_DAYS)

    if prices.empty:
        print("ERROR: Failed to fetch price data", file=sys.stderr)
        sys.exit(1)

    print("Computing metrics...", file=sys.stderr)

    print("Fetching fundamentals...", file=sys.stderr)
    fundamentals = extract_fundamentals(FUNDAMENTALS_TICKERS)

    ratio_pairs = {}
    for pair in CONFIG["ratio_pairs"]:
        if pair["numerator"] in prices.columns and pair["denominator"] in prices.columns:
            ratio_pairs[pair["name"]] = extract_ratio_pair(prices, pair)

    zscores = {}
    for pair_name in CONFIG["zscore_pairs"]:
        pair = next((p for p in CONFIG["ratio_pairs"] if p["name"] == pair_name), None)
        if pair and pair["numerator"] in prices.columns and pair["denominator"] in prices.columns:
            zscores[pair_name] = extract_zscore(prices, pair)

    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d"),
        "trend_months": TREND_MONTHS,
        "heatmap": extract_heatmap(prices),
        "ratio_pairs": ratio_pairs,
        "zscores": zscores,
        "financialization": extract_financialization(),
        "fundamentals": fundamentals,
    }

    json_str = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(json_str)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(json_str)

    if args.archive:
        analysis_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis")
        os.makedirs(analysis_dir, exist_ok=True)
        month_str = datetime.now().strftime("%Y-%m")
        archive_path = os.path.join(analysis_dir, f"{month_str}-data.json")
        with open(archive_path, "w") as f:
            f.write(json_str)
        print(f"Archived to {archive_path}", file=sys.stderr)

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
