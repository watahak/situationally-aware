from __future__ import annotations

import json
from pathlib import Path

from ui.charts.heatmap import build_heatmap_echart
from ui.charts.ratio import build_ratio_echart
from ui.charts.zscore import build_zscore_echart
from ui.charts.financialization import build_financialization_echart
from ui.charts.sankey import build_sankey_echart
from ui.charts.butterfly import build_butterfly_echart
from ui.charts.gauges import build_gauges_echart

_CONTEXTS_DIR = Path(__file__).resolve().parent.parent.parent / "contexts"


def load_context(name: str) -> dict | None:
    path = _CONTEXTS_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


__all__ = [
    "build_heatmap_echart",
    "build_ratio_echart",
    "build_zscore_echart",
    "build_financialization_echart",
    "build_sankey_echart",
    "build_butterfly_echart",
    "build_gauges_echart",
    "load_context",
]
