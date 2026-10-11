from __future__ import annotations

from ui.chart_theme import get_chart_theme


def build_gauges_echart(ctx: dict, *, theme_mode: str = "dark") -> dict:
    t = get_chart_theme(theme_mode)
    p = t["palette"]

    d = ctx["data"]
    cta_val = d.get("cta_percentile", 50)

    gamma_text = d.get("dealer_gamma_spy", "neutral")
    gamma_val = 75 if gamma_text == "positive" else (25 if gamma_text == "negative" else 50)

    vol_text = d.get("vol_target_equity_alloc", "neutral")
    vol_val = 80 if vol_text == "elevated" else (50 if vol_text == "neutral" else 30)

    green = p["green"]
    red = p["red"]
    amber = p["amber"]
    gray = "rgba(148, 163, 184, 0.25)" if not t["is_light"] else "rgba(100, 116, 139, 0.25)"
    pointer_color = p["text"]

    gauge_common = {
        "startAngle": 180,
        "endAngle": 0,
        "min": 0,
        "max": 100,
        "splitNumber": 4,
        "pointer": {
            "length": "60%",
            "width": 5,
            "itemStyle": {"color": pointer_color},
        },
        "axisTick": {"show": False},
        "splitLine": {"show": False},
        "axisLabel": {"show": False},
        "anchor": {"show": True, "size": 10, "itemStyle": {"color": pointer_color}},
        "animationDuration": 1500,
        "animationEasing": "elasticOut",
    }

    return {
        "backgroundColor": "transparent",
        "series": [
            {
                **gauge_common,
                "type": "gauge",
                "center": ["17%", "65%"],
                "radius": "60%",
                "axisLine": {"lineStyle": {"width": 16, "color": [
                    [0.25, green], [0.75, gray], [0.95, amber], [1, red],
                ]}},
                "detail": {
                    "fontSize": 18,
                    "color": p["text"],
                    "fontFamily": "Inter, sans-serif",
                    "fontWeight": "bold",
                    "offsetCenter": [0, "25%"],
                    "formatter": f"{cta_val}th pct",
                },
                "title": {
                    "fontSize": 12,
                    "color": p["muted"],
                    "offsetCenter": [0, "48%"],
                },
                "data": [{"value": cta_val, "name": "Trend Followers"}],
            },
            {
                **gauge_common,
                "type": "gauge",
                "center": ["50%", "65%"],
                "radius": "60%",
                "axisLine": {"lineStyle": {"width": 16, "color": [
                    [0.30, red], [0.50, gray], [1, green],
                ]}},
                "detail": {
                    "fontSize": 18,
                    "color": p["text"],
                    "fontFamily": "Inter, sans-serif",
                    "fontWeight": "bold",
                    "offsetCenter": [0, "25%"],
                    "formatter": gamma_text.capitalize(),
                },
                "title": {
                    "fontSize": 12,
                    "color": p["muted"],
                    "offsetCenter": [0, "48%"],
                },
                "data": [{"value": gamma_val, "name": "Options Dealer Hedging"}],
            },
            {
                **gauge_common,
                "type": "gauge",
                "center": ["83%", "65%"],
                "radius": "60%",
                "axisLine": {"lineStyle": {"width": 16, "color": [
                    [0.30, red], [0.65, gray], [0.90, amber], [1, red],
                ]}},
                "detail": {
                    "fontSize": 18,
                    "color": p["text"],
                    "fontFamily": "Inter, sans-serif",
                    "fontWeight": "bold",
                    "offsetCenter": [0, "25%"],
                    "formatter": vol_text.capitalize(),
                },
                "title": {
                    "fontSize": 12,
                    "color": p["muted"],
                    "offsetCenter": [0, "48%"],
                },
                "data": [{"value": vol_val, "name": "Volatility-Based Funds"}],
            },
        ],
    }
