from __future__ import annotations

import streamlit as st

_ECHART_INVIEW = st.components.v2.component(
    "echart_inview",
    html="""
<div data-role="chart-slot" style="width:100%;height:100%;"></div>
""",
    js="""
const ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js";

function loadEcharts() {
    if (window.echarts) return Promise.resolve(window.echarts);
    if (window.__miniQuantEchartsPromise) return window.__miniQuantEchartsPromise;
    window.__miniQuantEchartsPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = ECHARTS_CDN;
        script.async = true;
        script.onload = () => resolve(window.echarts);
        script.onerror = () => reject(new Error("Failed to load ECharts"));
        document.head.appendChild(script);
    });
    return window.__miniQuantEchartsPromise;
}

const instances =
    window.__miniQuantEchartInViewInstances ||
    (window.__miniQuantEchartInViewInstances = new WeakMap());

export default function (component) {
    const parentElement = component.parentElement;
    const data = component.data || {};
    if (!parentElement) return;

    const height = Number(data.height || 390);
    const rawThreshold = Number(data.threshold);
    const threshold =
        Number.isFinite(rawThreshold) ? Math.max(0, Math.min(1, rawThreshold)) : 0.35;
    const option = data.option || null;
    const alt = data.alt || "Chart";

    let state = instances.get(parentElement);
    if (!state) {
        const root =
            parentElement.querySelector('[data-role="chart-slot"]') ||
            parentElement.firstElementChild ||
            parentElement;
        state = {
            root,
            chart: null,
            observer: null,
            mounted: false,
            latestOption: null,
            resizeHandler: null,
        };
        instances.set(parentElement, state);
    }

    if (!state.root) return;
    state.root.style.width = "100%";
    state.root.style.height = `${height}px`;
    state.root.setAttribute("role", "img");
    state.root.setAttribute("aria-label", alt);
    state.latestOption = option;

    function mountChart() {
        if (!state.latestOption) return;

        loadEcharts()
            .then((echarts) => {
                if (!echarts) return;

                if (!state.chart) {
                    state.chart = echarts.init(state.root, null, { renderer: "canvas" });
                    state.resizeHandler = () => {
                        if (state.chart) state.chart.resize();
                    };
                    window.addEventListener("resize", state.resizeHandler);
                }

                state.chart.clear();
                state.chart.setOption(state.latestOption, true);
                state.mounted = true;
            })
            .catch(() => {
                // Keep the slot quiet if CDN load fails.
            });
    }

    if (!state.mounted) {
        if (state.observer) state.observer.disconnect();
        state.observer = new IntersectionObserver(
            (entries, obs) => {
                const entry = entries[0];
                if (entry && entry.isIntersecting) {
                    obs.disconnect();
                    state.observer = null;
                    mountChart();
                }
            },
            { threshold }
        );
        state.observer.observe(state.root);
    } else {
        mountChart();
    }

    return () => {
        if (state.observer) {
            state.observer.disconnect();
            state.observer = null;
        }
        if (state.chart) {
            state.chart.dispose();
            state.chart = null;
        }
        if (state.resizeHandler) {
            window.removeEventListener("resize", state.resizeHandler);
            state.resizeHandler = null;
        }
        instances.delete(parentElement);
    };
}
""",
)


def render_echart_inview(
    option: dict,
    *,
    key: str,
    height: int = 390,
    threshold: float = 0.35,
    alt: str = "Chart",
) -> None:
    _ECHART_INVIEW(
        key=key,
        data={"option": option, "height": height, "threshold": threshold, "alt": alt},
        width="stretch",
        height=height,
    )
