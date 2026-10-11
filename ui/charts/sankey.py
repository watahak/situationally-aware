from __future__ import annotations

from ui.chart_theme import get_chart_theme


def build_sankey_echart(ctx: dict, *, theme_mode: str = "dark") -> dict:
    t = get_chart_theme(theme_mode)
    p = t["palette"]

    d = ctx["data"]
    capex_split = d.get("capex_by_company", {})
    breakdown = d.get("intercompany_breakdown_bn", {})
    hw_total = breakdown.get("ai_hardware", 0)
    cloud_total = breakdown.get("cloud_compute", 0)
    ads_total = breakdown.get("digital_ads", 0)

    capex_sum = sum(capex_split.values()) or 1
    nodes = []
    links = []

    accent_base = (56, 189, 248) if not t["is_light"] else (2, 132, 199)
    companies = list(capex_split.keys())
    opacities = [0.9, 0.7, 0.55, 0.4]

    category_labels = {"ai_hardware": "AI Hardware", "cloud_compute": "Cloud Compute", "digital_ads": "Digital Ads"}
    category_display = [category_labels[k] for k in breakdown]

    node_colors = {}
    for i, co in enumerate(companies):
        op = opacities[i] if i < len(opacities) else 0.4
        node_colors[co] = f"rgba({accent_base[0]}, {accent_base[1]}, {accent_base[2]}, {op})"
    for cat in category_display:
        node_colors[cat] = p["amber"]
    node_colors["NVDA"] = p["green"]
    node_colors["Intercompany"] = p["muted"]

    all_node_names = companies + category_display + ["NVDA", "Intercompany"]
    for node_name in all_node_names:
        nodes.append({"name": node_name, "itemStyle": {"color": node_colors.get(node_name, p["accent"])}})

    category_totals = list(breakdown.values())
    for co, capex in capex_split.items():
        share = capex / capex_sum
        for cat_label, cat_total in zip(category_display, category_totals):
            links.append({"source": co, "target": cat_label, "value": round(cat_total * share)})

    links.append({"source": "AI Hardware", "target": "NVDA", "value": hw_total})
    links.append({"source": "Cloud Compute", "target": "Intercompany", "value": cloud_total})
    links.append({"source": "Digital Ads", "target": "Intercompany", "value": ads_total})

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "item",
            "triggerOn": "mousemove",
            "backgroundColor": p["slate"],
            "borderColor": t["echart_border"],
            "textStyle": {"color": p["text"], "fontSize": 13},
        },
        "series": [{
            "type": "sankey",
            "orient": "horizontal",
            "layoutIterations": 32,
            "nodeWidth": 24,
            "nodeGap": 14,
            "data": nodes,
            "links": links,
            "emphasis": {"focus": "adjacency"},
            "lineStyle": {"color": "gradient", "curveness": 0.5, "opacity": 0.35},
            "label": {
                "color": p["text"],
                "fontSize": 12,
                "fontFamily": "Inter, sans-serif",
                "formatter": "{b}\n${c}B",
            },
            "animationDuration": 1200,
            "animationEasing": "cubicOut",
        }],
    }
