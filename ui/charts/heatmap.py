from __future__ import annotations

import numpy as np
import pandas as pd

from core import e
from ui.chart_theme import get_chart_theme


def build_heatmap_echart(roc_df: pd.DataFrame, *, theme_mode: str = "dark") -> dict:
    t = get_chart_theme(theme_mode)
    p = t["palette"]

    cols = roc_df.columns.tolist()
    rows = [e(ticker) for ticker in roc_df.index]
    if not cols or not rows:
        return {
            "backgroundColor": "transparent",
            "title": {
                "text": "No heatmap data available",
                "left": "center",
                "top": "middle",
                "textStyle": {"color": p["muted"], "fontSize": 14, "fontWeight": 400},
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
                        "color": p["text"],
                    },
                })
            else:
                column_points.append({"value": [x, y, None], "label": {"show": False}})

        column_series.append({
            "name": window,
            "type": "heatmap",
            "data": column_points,
            "itemStyle": {
                "borderColor": t["echart_cell_border"],
                "borderWidth": 1,
            },
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 8,
                    "shadowColor": t["echart_shadow"],
                }
            },
            "animationDuration": 700,
            "animationDelay": x * 120,
            "animationEasing": "cubicOut",
        })

    if not np.isfinite(min_val) or not np.isfinite(max_val):
        min_val, max_val = -1.0, 1.0

    bound = max(abs(min_val), abs(max_val), 1.0)

    return {
        "backgroundColor": "transparent",
        "grid": {"left": "2%", "right": "1%", "top": "6%", "bottom": "18%", "containLabel": True},
        "tooltip": {
            "position": "top",
            "backgroundColor": p["slate"],
            "borderColor": t["echart_border"],
            "textStyle": {"color": p["text"], "fontSize": 13},
        },
        "xAxis": {
            "type": "category",
            "position": "top",
            "data": cols,
            "axisTick": {"show": False},
            "axisLine": {"lineStyle": {"color": t["echart_line"]}},
            "axisLabel": {
                "color": p["muted"],
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
            "axisLine": {"lineStyle": {"color": t["echart_line"]}},
            "axisLabel": {"color": p["text"], "fontSize": 12, "margin": 6},
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
            "textStyle": {"color": p["muted"], "fontSize": 11},
            "inRange": {"color": [p["red"], p["slate"], p["green"]]},
        },
        "series": column_series,
    }
