from __future__ import annotations

import numpy as np
import pandas as pd

from settings.market import CONFIG
from ui.chart_theme import get_chart_theme


def build_zscore_echart(
    zscore: pd.Series,
    thresholds: tuple[float, float],
    pair_name: str,
    *,
    theme_mode: str = "dark",
) -> dict:
    t = get_chart_theme(theme_mode)
    p = t["palette"]

    lo, hi = thresholds
    dates = [d.strftime("%Y-%m-%d") for d in zscore.index]

    bars: list[dict] = []
    finite_values: list[float] = []
    for raw_value in zscore.values:
        if pd.notna(raw_value) and np.isfinite(raw_value):
            value = round(float(raw_value), 4)
            finite_values.append(abs(value))
            if value <= lo:
                color = p["red"]
            elif value >= hi:
                color = p["green"]
            else:
                color = t["zscore_neutral_bar"]
            bars.append({"value": value, "itemStyle": {"color": color}})
        else:
            bars.append({"value": None, "itemStyle": {"color": t["zscore_neutral_bar_faint"]}})

    y_max = max(finite_values) + 0.5 if finite_values else 4.0
    y_max = max(y_max, 4.0)

    return {
        "backgroundColor": "transparent",
        "title": {
            "text": f"{pair_name} - {CONFIG['zscore_window']}-Day Z-Score",
            "left": "1%",
            "top": "2%",
            "textStyle": {"color": p["text"], "fontSize": 16, "fontWeight": 500},
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": p["slate"],
            "borderColor": t["echart_border"],
            "textStyle": {"color": p["text"], "fontSize": 13},
        },
        "grid": {"left": "4%", "right": "3%", "top": "20%", "bottom": "16%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": dates,
            "axisTick": {"show": False},
            "axisLine": {"lineStyle": {"color": t["echart_line"]}},
            "axisLabel": {"color": p["muted"], "fontSize": 11, "hideOverlap": True},
            "splitLine": {"show": False},
        },
        "yAxis": {
            "type": "value",
            "min": -y_max,
            "max": y_max,
            "axisLine": {"show": False},
            "axisLabel": {"color": p["muted"], "fontSize": 11},
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
                        [{"yAxis": -1, "itemStyle": {"color": t["zscore_band_neutral"]}}, {"yAxis": 1}],
                        [{"yAxis": 1, "itemStyle": {"color": t["zscore_band_warning"]}}, {"yAxis": 2}],
                        [{"yAxis": -2, "itemStyle": {"color": t["zscore_band_warning"]}}, {"yAxis": -1}],
                        [{"yAxis": 2, "itemStyle": {"color": t["zscore_band_risk"]}}, {"yAxis": y_max}],
                        [{"yAxis": -y_max, "itemStyle": {"color": t["zscore_band_risk"]}}, {"yAxis": -2}],
                    ],
                },
                "markLine": {
                    "silent": True,
                    "symbol": "none",
                    "lineStyle": {"width": 1},
                    "data": [
                        {
                            "yAxis": hi,
                            "lineStyle": {"type": "dashed", "color": p["green"]},
                            "label": {
                                "show": True,
                                "formatter": f"+{hi:g}",
                                "color": p["green"],
                                "position": "insideEndTop",
                                "distance": 6,
                            },
                        },
                        {
                            "yAxis": lo,
                            "lineStyle": {"type": "dashed", "color": p["red"]},
                            "label": {
                                "show": True,
                                "formatter": f"{lo:g}",
                                "color": p["red"],
                                "position": "insideEndBottom",
                                "distance": 6,
                            },
                        },
                        {
                            "yAxis": 0,
                            "lineStyle": {"type": "solid", "color": p["muted"], "width": 0.5},
                            "label": {"show": False},
                        },
                    ],
                },
            }
        ],
    }
