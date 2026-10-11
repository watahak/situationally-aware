from __future__ import annotations

import pandas as pd

from ui.chart_theme import get_chart_theme


def build_financialization_echart(gap_df: pd.DataFrame, *, theme_mode: str = "dark") -> dict:
    t = get_chart_theme(theme_mode)
    p = t["palette"]

    labels = gap_df["label"].tolist()
    gdp_vals = [round(float(v), 1) for v in gap_df["gdp_pct"]]
    mcap_vals = [round(float(v), 1) for v in gap_df["mcap_pct"]]

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": p["slate"],
            "borderColor": t["echart_border"],
            "textStyle": {"color": p["text"], "fontSize": 13},
        },
        "legend": {
            "data": ["GDP Share (%)", "Market Cap Weight (%)"],
            "left": "0%",
            "top": "0%",
            "textStyle": {"color": p["muted"], "fontSize": 11},
        },
        "grid": {"left": "8%", "right": "10%", "top": "12%", "bottom": "10%", "containLabel": True},
        "xAxis": {
            "type": "value",
            "name": "Share of Global Total (%)",
            "nameLocation": "middle",
            "nameGap": 30,
            "nameTextStyle": {"color": p["muted"], "fontSize": 12},
            "axisLabel": {"color": p["muted"], "fontSize": 11},
            "splitLine": {"lineStyle": {"color": p["grid"]}},
            "axisLine": {"show": False},
        },
        "yAxis": {
            "type": "category",
            "data": labels,
            "inverse": True,
            "axisLabel": {"color": p["text"], "fontSize": 12},
            "axisLine": {"lineStyle": {"color": t["echart_line"]}},
            "splitLine": {"show": False},
        },
        "series": [
            {
                "name": "GDP Share (%)",
                "type": "bar",
                "data": gdp_vals,
                "itemStyle": {"color": p["accent"], "borderRadius": [0, 3, 3, 0]},
                "label": {
                    "show": True, "position": "right",
                    "formatter": "{c}%",
                    "color": p["text"], "fontSize": 11,
                },
                "animationDuration": 1200,
                "animationEasing": "cubicOut",
            },
            {
                "name": "Market Cap Weight (%)",
                "type": "bar",
                "data": mcap_vals,
                "itemStyle": {"color": p["red"], "borderRadius": [0, 3, 3, 0]},
                "label": {
                    "show": True, "position": "right",
                    "formatter": "{c}%",
                    "color": p["text"], "fontSize": 11,
                },
                "animationDuration": 1200,
                "animationDelay": 300,
                "animationEasing": "cubicOut",
            },
        ],
    }
