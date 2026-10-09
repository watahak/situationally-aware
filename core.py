from numbers import Integral

import numpy as np
import pandas as pd

from settings.market import (
    CONFIG,
    ROTATION_FLAT_TOLERANCE,
)


def e(ticker: str) -> str:
    return f"{CONFIG['ticker_emoji'].get(ticker, '')} {ticker}"


def pair_display_name(pair: dict) -> str:
    return f"{e(pair['numerator'])} / {e(pair['denominator'])}"


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
