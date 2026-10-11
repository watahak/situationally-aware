from __future__ import annotations

from ui.chart_theme import get_chart_theme


def build_butterfly_echart(physical: dict, fin_regions: list, *, theme_mode: str = "dark") -> dict:
    t = get_chart_theme(theme_mode)
    p = t["palette"]

    rows = []
    for region_key, label in [("us", "US"), ("china", "China")]:
        energy = physical.get(f"{region_key}_energy_pct", 0)
        mfg = physical.get(f"{region_key}_manufacturing_pct", 0)
        mcap = 0
        for r in fin_regions:
            if r["label"] == label:
                mcap = r["mcap_pct"]
                break
        rows.append({"label": label, "energy": energy, "mfg": mfg, "mcap": mcap})

    eu_energy = physical.get("europe_energy_pct", 0)
    eu_mfg = physical.get("europe_manufacturing_pct", 0)
    for r in fin_regions:
        if r["label"] == "Europe":
            rows.append({"label": "Europe", "energy": eu_energy, "mfg": eu_mfg, "mcap": r["mcap_pct"]})
            break

    labels = [r["label"] for r in rows]
    energy_data = [{"value": -r["energy"], "label": {"formatter": f"{r['energy']}%"}} for r in rows]
    mfg_data = [{"value": -r["mfg"], "label": {"formatter": f"{r['mfg']}%"}} for r in rows]
    mcap_data = [{"value": r["mcap"], "label": {"formatter": f"{r['mcap']}%"}} for r in rows]

    amber1 = p["amber"]
    amber2 = "rgba(251, 191, 36, 0.55)" if not t["is_light"] else "rgba(217, 119, 6, 0.55)"

    raw_phys = [r["energy"] + r["mfg"] for r in rows]
    raw_mcap = [r["mcap"] for r in rows]
    max_val = max(max(raw_phys), max(raw_mcap)) + 8

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
            "data": ["Energy Consumption %", "Manufacturing %", "Market Cap Weight %"],
            "left": "center",
            "top": "0%",
            "textStyle": {"color": p["muted"], "fontSize": 11},
        },
        "grid": {"left": "3%", "right": "3%", "top": "14%", "bottom": "6%", "containLabel": True},
        "graphic": [
            {"type": "text", "left": "8%", "bottom": "0%", "style": {"text": "← Physical Economy", "fill": p["muted"], "fontSize": 11}},
            {"type": "text", "right": "8%", "bottom": "0%", "style": {"text": "Financial Weight →", "fill": p["muted"], "fontSize": 11}},
        ],
        "xAxis": {
            "type": "value",
            "min": -max_val,
            "max": max_val,
            "axisLabel": {"show": False},
            "splitLine": {"show": False},
            "axisLine": {"show": False},
        },
        "yAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"color": p["text"], "fontSize": 13, "fontWeight": "bold"},
            "axisLine": {"lineStyle": {"color": t["echart_line"]}},
            "axisTick": {"show": False},
            "splitLine": {"show": False},
        },
        "series": [
            {
                "name": "Energy Consumption %",
                "type": "bar",
                "stack": "physical",
                "data": energy_data,
                "itemStyle": {"color": amber1, "borderRadius": [3, 0, 0, 3]},
                "label": {
                    "show": True,
                    "position": "left",
                    "color": p["text"],
                    "fontSize": 11,
                },
                "animationDuration": 1200,
                "animationEasing": "cubicOut",
            },
            {
                "name": "Manufacturing %",
                "type": "bar",
                "stack": "physical",
                "data": mfg_data,
                "itemStyle": {"color": amber2},
                "label": {
                    "show": True,
                    "position": "left",
                    "color": p["text"],
                    "fontSize": 11,
                },
                "animationDuration": 1200,
                "animationDelay": 200,
                "animationEasing": "cubicOut",
            },
            {
                "name": "Market Cap Weight %",
                "type": "bar",
                "data": mcap_data,
                "itemStyle": {"color": p["accent"], "borderRadius": [0, 3, 3, 0]},
                "label": {
                    "show": True,
                    "position": "right",
                    "color": p["text"],
                    "fontSize": 11,
                },
                "animationDuration": 1200,
                "animationDelay": 400,
                "animationEasing": "cubicOut",
            },
        ],
    }
