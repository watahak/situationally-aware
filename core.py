from numbers import Integral

import numpy as np
import pandas as pd


CONFIG = {
    "us_concentration": ["SPY", "RSP", "QQQ", "QQQE"],
    "global_geographic": ["VXUS", "EEM", "EWS", "MCHI", "KWEB", "VGK"],
    "safe_havens": ["GLD", "TLT", "TIP"],

    "heatmap_tickers": ["SPY", "RSP", "QQQ", "QQQE", "VXUS", "EEM", "EWS", "MCHI", "KWEB", "VGK", "GLD", "TLT", "TIP"],

    "ticker_legend": {
        "SPY": "S&P 500 (cap-weighted US large-cap)",
        "RSP": "S&P 500 Equal Weight",
        "QQQ": "Nasdaq 100 (cap-weighted US tech-heavy)",
        "QQQE": "Nasdaq 100 Equal Weight",
        "VXUS": "Vanguard Total International Stock ETF (ex-US equities)",
        "EEM": "iShares MSCI Emerging Markets",
        "EWS": "iShares MSCI Singapore",
        "MCHI": "iShares MSCI China",
        "KWEB": "KraneShares CSI China Internet (Chinese big tech)",
        "VGK": "Vanguard FTSE Europe",
        "GLD": "SPDR Gold Shares (physical gold proxy)",
        "TLT": "iShares 20+ Year US Treasury Bonds",
        "TIP": "iShares TIPS Bond ETF (inflation-protected Treasuries)",
    },

    "ticker_emoji": {
        "SPY": "🇺🇸", "RSP": "🇺🇸", "QQQ": "🇺🇸", "QQQE": "🇺🇸",
        "VXUS": "🌐", "EEM": "🌏", "EWS": "🇸🇬", "MCHI": "🇨🇳",
        "KWEB": "🇨🇳", "VGK": "🇪🇺",
        "GLD": "🥇", "TLT": "🏛️", "TIP": "🏛️",
    },

    "roc_windows": [
        ("1W", 5, 0),
        ("1M", 21, 0),
        ("3M", 63, 0),
        ("6M", 126, 0),
        ("1Y", 252, 365),
        ("2Y", 504, 730),
        ("5Y", 1260, 1825),
    ],

    "ratio_pairs": [
        {
            "name": "SPY / RSP",
            "numerator": "SPY",
            "denominator": "RSP",
            "tooltip": (
                "**SPY / RSP** compares cap-weighted with equal-weight S&P 500 "
                "performance. A **rising** line means SPY is outperforming; a "
                "**falling** line means RSP is outperforming. This is a relative "
                "breadth/concentration proxy, not proof of flows or a broad rally; "
                "both ETFs can fall. "
                "This ratio serves as a concentration proxy: when cap-weighted pulls "
                "ahead of equal-weight, index returns are being driven by fewer, "
                "larger names — a structural signal of passive-flow concentration."
            ),
        },
        {
            "name": "QQQ / QQQE",
            "numerator": "QQQ",
            "denominator": "QQQE",
            "tooltip": (
                "**QQQ / QQQE** compares cap-weighted with equal-weight Nasdaq "
                "100 performance. A **rising** line means QQQ is outperforming; "
                "a **falling** line means QQQE is outperforming. Relative price "
                "performance does not measure passive inflows or establish "
                "their cause. "
                "A tech-sector concentration gauge. Widening divergence suggests "
                "mega-cap names are absorbing a disproportionate share of passive "
                "index inflows relative to the broader Nasdaq 100 constituents."
            ),
        },
        {
            "name": "VXUS / SPY",
            "numerator": "VXUS",
            "denominator": "SPY",
            "tooltip": (
                "**VXUS / SPY** compares ex-US equities with US large-cap "
                "equities. A **rising** line means VXUS is outperforming; a "
                "**falling** line means SPY is outperforming. USD-listed ETF "
                "returns include currency effects and do not verify capital "
                "moving between regions. "
                "Tracks the relative performance of international vs. US "
                "large-cap equities. A sustained shift in this ratio can "
                "indicate early-stage geographic rebalancing in global allocations."
            ),
        },
        {
            "name": "EWS / EEM",
            "numerator": "EWS",
            "denominator": "EEM",
            "tooltip": (
                "**EWS / EEM** compares developed-market Singapore equities "
                "with emerging-market equities. A **rising** line means EWS "
                "is outperforming; a **falling** line means EEM is outperforming. "
                "USD-listed ETF returns include currency and sector effects; "
                "the ratio alone does not identify flows or their causes. "
                "Singapore is a developed-market financial hub benchmarked against "
                "the broader EM universe. Relative strength here can reflect "
                "trade-flow positioning and USD funding conditions in Asia."
            ),
        },
        {
            "name": "KWEB / MCHI",
            "numerator": "KWEB",
            "denominator": "MCHI",
            "tooltip": (
                "**KWEB / MCHI** compares Chinese internet equities with broad "
                "China equities, with overlapping exposures. A **rising** line "
                "means KWEB is outperforming; a **falling** line means MCHI is "
                "outperforming. This does not establish sector flows or "
                "regulatory causes. "
                "Compares Chinese internet equities against broad China exposure. "
                "Divergence often reflects regulatory risk repricing or "
                "sector-specific capital rotation within the Chinese market."
            ),
        },
        {
            "name": "KWEB / QQQ",
            "numerator": "KWEB",
            "denominator": "QQQ",
            "tooltip": (
                "**KWEB / QQQ** compares Chinese internet equities with the "
                "US tech-heavy Nasdaq 100. A **rising** line means KWEB is "
                "outperforming; a **falling** line means QQQ is outperforming. "
                "The ratio is a relative-performance proxy, not measured "
                "cross-border flows or evidence of a particular cause. "
                "A US-vs-China technology leadership proxy. Structural divergence "
                "can reflect index-rule constraints, delisting risk, or forced "
                "rebalancing rather than pure sentiment shifts."
            ),
        },
        {
            "name": "GLD / TLT",
            "numerator": "GLD",
            "denominator": "TLT",
            "tooltip": (
                "**GLD / TLT** compares gold with long-duration US Treasuries. "
                "A **rising** line means GLD is outperforming; a **falling** line "
                "means TLT is outperforming. Relative prices alone do not "
                "establish inflation expectations, de-dollarization, or "
                "transfers between these assets. "
                "A real-asset vs. sovereign-duration proxy. Persistent gold "
                "outperformance relative to long-dated Treasuries can indicate "
                "shifting confidence in sovereign credit or duration risk appetite."
            ),
        },
    ],

    "zscore_pairs": ["SPY / RSP", "QQQ / QQQE", "VXUS / SPY", "EWS / EEM", "KWEB / MCHI", "KWEB / QQQ", "GLD / TLT"],
    "zscore_window": 60,
    "zscore_thresholds": (-2, 2),

    "sma_lengths": [50, 200],
}

MACRO_ANCHORS = {
    "last_updated": "YYYY-QN",
    "gdp_source": "IMF WEO",
    "mcap_source": "MSCI ACWI Factsheet",
    "regions": [
        {"label": "US",        "etf": "SPY",  "gdp_pct": 26.0, "mcap_pct": 63.0},
        {"label": "Europe",    "etf": "VGK",  "gdp_pct": 17.0, "mcap_pct": 14.0},
        {"label": "China",     "etf": "MCHI", "gdp_pct": 17.5, "mcap_pct":  3.5},
        {"label": "EM ex-CN",  "etf": "EEM",  "gdp_pct": 25.0, "mcap_pct":  9.0},
        {"label": "Singapore", "etf": "EWS",  "gdp_pct":  0.5, "mcap_pct":  0.4},
    ],
}

FUNDAMENTALS_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOG", "AMZN", "META", "TSLA"]


def e(ticker: str) -> str:
    return f"{CONFIG['ticker_emoji'].get(ticker, '')} {ticker}"


def pair_display_name(pair: dict) -> str:
    return f"{e(pair['numerator'])} / {e(pair['denominator'])}"

LOOKBACK_MAP = {"1 Year": 365, "2 Years": 730, "5 Years": 1825}


def get_all_tickers() -> list[str]:
    """Deduplicated, sorted list of every ticker referenced in CONFIG."""
    tickers = set()
    tickers.update(CONFIG["us_concentration"])
    tickers.update(CONFIG["global_geographic"])
    tickers.update(CONFIG["safe_havens"])
    for pair in CONFIG["ratio_pairs"]:
        tickers.add(pair["numerator"])
        tickers.add(pair["denominator"])
    return sorted(tickers)


# Numerical zero only, in percentage points; not an economic significance filter.
ROTATION_FLAT_TOLERANCE = 1e-10


def _validate_sessions(n_sessions: int) -> None:
    if isinstance(n_sessions, bool) or not isinstance(n_sessions, Integral) or n_sessions <= 0:
        raise ValueError("n_sessions must be a positive integer")


def _prepare_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Sort a copy on shared dates without filling or dropping missing quotes."""
    frame = prices.copy()
    frame.index = pd.DatetimeIndex(frame.index)
    if frame.index.has_duplicates:
        raise ValueError("Price index contains duplicate dates")
    if frame.index.hasnans:
        raise ValueError("Price index contains missing dates")
    return frame.sort_index().apply(pd.to_numeric, errors="coerce").astype(float)


def _endpoint_returns(prices: pd.DataFrame, start: int | None, end: int | None) -> pd.Series:
    if start is None or end is None:
        return pd.Series(np.nan, index=prices.columns, dtype=float)
    first, last = prices.iloc[start], prices.iloc[end]
    valid = np.isfinite(first) & first.gt(0) & np.isfinite(last) & last.gt(0)
    return ((last.where(valid) / first.where(valid) - 1) * 100).replace(
        [np.inf, -np.inf], np.nan
    )


def calc_roc_table(
    prices: pd.DataFrame,
    roc_windows: list[tuple],
) -> pd.DataFrame:
    """Ticker returns (%) over n shared trading intervals, requiring n+1 rows.

    Endpoints must be finite and strictly positive. Missing endpoint prices are
    never filled or backdated; interior gaps do not invalidate endpoint returns.
    """
    prices = _prepare_prices(prices)
    records = {}
    for label, n_sessions, *_ in roc_windows:
        _validate_sessions(n_sessions)
        start = len(prices) - n_sessions - 1 if len(prices) > n_sessions else None
        end = len(prices) - 1 if len(prices) else None
        records[label] = _endpoint_returns(prices, start, end)
    return pd.DataFrame(records, index=prices.columns)


def calc_rotation_table(prices: pd.DataFrame, n_sessions: int) -> pd.DataFrame:
    """Relative ETF performance for every configured pair, including unavailable pairs.

    Dates are sorted and shared by all pairs; duplicate dates are rejected.
    Current endpoints are [-n-1, -1], previous endpoints [-2n-1, -n-1].
    Returns and canonical A/B changes are percentages, not measured fund flows.
    A ratio change within 1e-10 percentage points of zero is numerically flat.
    Coverage counts rows where both legs are finite and positive; missing interior
    observations do not invalidate endpoint returns. No filling or backdating.
    """
    _validate_sessions(n_sessions)
    prices = _prepare_prices(prices)
    original_columns = prices.columns
    tickers = sorted({pair[leg] for pair in CONFIG["ratio_pairs"]
                      for leg in ("numerator", "denominator")})
    prices = prices.reindex(columns=tickers)
    valid = np.isfinite(prices) & prices.gt(0)
    last_valid = {
        ticker: prices.index[valid[ticker]][-1] if valid[ticker].any() else pd.NaT
        for ticker in tickers
    }
    size = len(prices)
    end = size - 1 if size else None
    start = size - n_sessions - 1 if size > n_sessions else None
    previous_start = size - 2 * n_sessions - 1 if size > 2 * n_sessions else None
    current_returns = _endpoint_returns(prices, start, end)
    previous_returns = _endpoint_returns(prices, previous_start, start)

    def window_result(pair, first, last, returns, required_rows):
        numerator, denominator = pair["numerator"], pair["denominator"]
        coverage = 0
        if last is not None:
            observed = valid.iloc[first if first is not None else 0:last + 1]
            coverage = int((observed[numerator] & observed[denominator]).sum())
        result = {
            "start_date": prices.index[first] if first is not None else pd.NaT,
            "end_date": prices.index[last] if last is not None else pd.NaT,
            "numerator_return": returns[numerator],
            "denominator_return": returns[denominator],
            "ratio_change": np.nan,
            "leader": None,
            "laggard": None,
            "status": "Valid",
            "coverage": coverage,
        }
        if first is None or last is None:
            result["status"] = f"Insufficient history: need {required_rows} rows, have {size}"
            return result

        reasons = []
        for ticker in (numerator, denominator):
            if ticker not in original_columns:
                reasons.append(f"Missing column: {ticker}")
                continue
            for label, position in (("start", first), ("end", last)):
                value = prices.iloc[position][ticker]
                if pd.isna(value):
                    reasons.append(f"Missing {label} price: {ticker}")
                elif not valid.iloc[position][ticker]:
                    reasons.append(f"Invalid {label} price: {ticker} (requires finite positive)")
        if reasons:
            result["status"] = "; ".join(reasons)
            return result

        # Preserve canonical A/B sign even when the denominator is the leader.
        first_ratio = prices.iloc[first][numerator] / prices.iloc[first][denominator]
        last_ratio = prices.iloc[last][numerator] / prices.iloc[last][denominator]
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            change = float((last_ratio / first_ratio - 1) * 100)
        if not np.isfinite(change):
            result["status"] = "Non-finite ratio change"
            return result
        result["ratio_change"] = change
        if change > ROTATION_FLAT_TOLERANCE:
            result["leader"], result["laggard"] = numerator, denominator
        elif change < -ROTATION_FLAT_TOLERANCE:
            result["leader"], result["laggard"] = denominator, numerator
        return result

    records = []
    for pair in CONFIG["ratio_pairs"]:
        current = window_result(pair, start, end, current_returns, n_sessions + 1)
        previous = window_result(pair, previous_start, start, previous_returns, 2 * n_sessions + 1)
        if current["status"] != "Valid":
            transition = "Current window unavailable"
        elif previous["status"] != "Valid":
            transition = "Previous window unavailable"
        elif current["leader"] is None and previous["leader"] is None:
            transition = "Flat in both"
        elif previous["leader"] is None:
            transition = "Emerged from flat"
        elif current["leader"] is None:
            transition = "Became flat"
        elif current["leader"] == previous["leader"]:
            transition = "Same leader"
        else:
            transition = "Opposite leader"
        records.append({
            "name": pair["name"],
            "numerator": pair["numerator"],
            "denominator": pair["denominator"],
            **current,
            "expected_observations": n_sessions + 1,
            "numerator_last_valid": last_valid[pair["numerator"]],
            "denominator_last_valid": last_valid[pair["denominator"]],
            **{f"previous_{key}": value for key, value in previous.items()},
            "transition": transition,
        })
    return pd.DataFrame(records)


def calc_ratio(prices: pd.DataFrame, numerator: str, denominator: str) -> pd.Series:
    """Element-wise price ratio.  Inf values replaced with NaN."""
    ratio = prices[numerator] / prices[denominator]
    return ratio.replace([np.inf, -np.inf], np.nan).dropna()


def calc_sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average.  No partial-window values (min_periods=window)."""
    return series.rolling(window, min_periods=window).mean()


def calc_zscore(series: pd.Series, window: int) -> pd.Series:
    """Rolling Z-score: (x - μ_rolling) / σ_rolling."""
    rolling_mean = series.rolling(window, min_periods=window).mean()
    rolling_std = series.rolling(window, min_periods=window).std()
    return ((series - rolling_mean) / rolling_std).dropna()


def calc_financialization_gap(regions: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(regions)
    df["gap_pct"] = df["mcap_pct"] - df["gdp_pct"]
    return df
