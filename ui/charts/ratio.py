from __future__ import annotations

import pandas as pd

from ui.chart_theme import get_chart_theme


def build_ratio_echart(
    ratio: pd.Series,
    sma_dict: dict[str, pd.Series],
    pair_name: str,
    *,
    theme_mode: str = "dark",
) -> dict:
    t = get_chart_theme(theme_mode)
    p = t["palette"]

    dates = [d.strftime("%Y-%m-%d") for d in ratio.index]

    series = [
        {
            "name": pair_name,
            "type": "line",
            "data": [round(float(v), 5) for v in ratio.values],
            "smooth": 0.3,
            "symbol": "none",
            "lineStyle": {"color": p["accent"], "width": 2},
            "itemStyle": {"color": p["accent"]},
            "animationDuration": 1500,
            "animationEasing": "cubicOut",
        }
    ]

    sma_colors = {50: p["amber"], 200: p["red"]}
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
                "color": sma_colors.get(length, p["muted"]),
                "width": 1.5,
                "type": sma_dashes.get(length, [4, 4]),
            },
            "itemStyle": {"color": sma_colors.get(length, p["muted"])},
            "animationDuration": 1800,
            "animationDelay": 300 + i * 200,
            "animationEasing": "cubicOut",
        })

    return {
        "backgroundColor": "transparent",
        "title": {
            "text": pair_name,
            "left": "1%",
            "top": "2%",
            "textStyle": {"color": p["text"], "fontSize": 16, "fontWeight": 500},
        },
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": p["slate"],
            "borderColor": t["echart_border"],
            "textStyle": {"color": p["text"], "fontSize": 13},
        },
        "legend": {
            "data": [s["name"] for s in series],
            "orient": "horizontal",
            "left": "center",
            "bottom": "1%",
            "textStyle": {"color": p["muted"], "fontSize": 11},
        },
        "grid": {"left": "4%", "right": "3%", "top": "18%", "bottom": "20%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": dates,
            "axisLine": {"lineStyle": {"color": t["echart_line"]}},
            "axisLabel": {"color": p["muted"], "fontSize": 11},
            "splitLine": {"show": False},
        },
        "yAxis": {
            "type": "value",
            "scale": True,
            "axisLine": {"show": False},
            "axisLabel": {"color": p["muted"], "fontSize": 11},
            "splitLine": {"lineStyle": {"color": p["grid"]}},
        },
        "series": series,
        "animationDuration": 1500,
        "animationEasing": "cubicOut",
    }
