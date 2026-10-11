from __future__ import annotations

import ui.theme as theme_utils


def get_chart_theme(theme_mode: str) -> dict:
    palette = theme_utils.get_active_palette(theme_mode)
    is_light = theme_mode == "light"

    return {
        "palette": palette,
        "is_light": is_light,
        "echart_line": "rgba(15, 23, 42, 0.16)" if is_light else "rgba(255, 255, 255, 0.1)",
        "echart_border": "rgba(15, 23, 42, 0.18)" if is_light else "rgba(255, 255, 255, 0.1)",
        "echart_cell_border": "rgba(15, 23, 42, 0.12)" if is_light else "rgba(255,255,255,0.06)",
        "echart_shadow": "rgba(15, 23, 42, 0.22)" if is_light else "rgba(0,0,0,0.35)",
        "zscore_neutral_bar": "rgba(100, 116, 139, 0.42)" if is_light else "rgba(148, 163, 184, 0.4)",
        "zscore_neutral_bar_faint": "rgba(100, 116, 139, 0.22)" if is_light else "rgba(148, 163, 184, 0.2)",
        "zscore_band_neutral": "rgba(15, 23, 42, 0.06)" if is_light else "rgba(255, 255, 255, 0.03)",
        "zscore_band_warning": "rgba(217, 119, 6, 0.12)" if is_light else "rgba(234, 179, 8, 0.08)",
        "zscore_band_risk": "rgba(220, 38, 38, 0.14)" if is_light else "rgba(239, 68, 68, 0.12)",
    }
