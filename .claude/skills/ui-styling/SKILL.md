---
name: ui-styling
description: "Enforce sleek, professional dark-mode UI and advanced chart styling for Streamlit and Plotly analytical dashboards. Use when styling financial charts, adding z-score bands, metric cards, dark heatmaps, or container CSS animations in Python Streamlit apps."
---

# Streamlit & Plotly Dashboard UI Styling

A skill for transforming Python Streamlit and Plotly financial dashboards into polished, high-performance dark-mode analytics interfaces.

## When to Use

- Building or upgrading Streamlit dashboards with Plotly charts (streamlit>=1.35.0, plotly>=5.22.0).
- Styling financial data visualisations (line charts, z-scores, correlation heatmaps).
- Enhancing Streamlit layout architecture with card containers, glassmorphism, and scroll animations.

## Core Rules & Architecture

- Keep design professional and high-density. Avoid decorative fluff or neon gaudiness.
- Maintain a unified dark color palette (`#0E1117` base, `#161B22` cards, `#1E293B` slates, `#38BDF8` primary accents).
- Always remove heavy Plotly backgrounds and gridlines (`paper_bgcolor="rgba(0,0,0,0)"`, `plot_bgcolor="rgba(0,0,0,0)"`).

## Implementation Steps

### 1. Streamlit Layout & Card CSS

Inject custom CSS for translucent dark cards with soft elevation:

```python
import streamlit as st

st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] > div[data-testid="stBlock"] {
        background: rgba(22, 27, 34, 0.6);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stBlock"]:hover {
        border-color: rgba(56, 189, 248, 0.4);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)
```

Use `st.container(border=True)` to house metrics and charts cleanly inside cards.

### 2. Plotly Line Charts & Fills

- Use smooth spline curves (`shape='spline'`).
- Add translucent area gradient fills (`fill='tozeroy'`, `fillcolor='rgba(56, 189, 248, 0.08)'`).
- Clean up axis lines and style hover labels.

```python
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['Date'], y=df['Price'],
    mode='lines',
    line=dict(color='#38BDF8', width=2.5, shape='spline'),
    fill='tozeroy',
    fillcolor='rgba(56, 189, 248, 0.08)',
    hovertemplate="<b>Date:</b> %{x|%b %d, %Y}<br><b>Price:</b> $%{y:.2f}<extra></extra>"
))
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", zeroline=False),
    hoverlabel=dict(bgcolor="#1E293B", font_size=13, font_family="Inter, sans-serif")
)
```

### 3. Z-Score Anomaly Charts

Use horizontal rectangle overlays (`add_hrect`) for sigma bands (+/- 1 sigma, +/- 2 sigma, +/- 3 sigma).

Use subtle translucent colors:

| Band | Color |
|---|---|
| Neutral (+/- 1 sigma) | `rgba(255, 255, 255, 0.03)` |
| Warning (+/- 1 to +/- 2 sigma) | `rgba(234, 179, 8, 0.08)` |
| Anomaly (> +/- 2 sigma) | `rgba(239, 68, 68, 0.12)` |

### 4. Correlation Heatmaps

- Use clean cell gaps (`xgap=2`, `ygap=2`).
- Apply a dark divergent palette (`#EF4444` -> `#1E293B` -> `#10B981`).
- Display clean formatted numerical overlays (`texttemplate="%{z:.2f}"`).

### 5. Smooth Entrance Micro-Animations

Inject CSS keyframes for fade-and-slide entry without JS libraries:

```python
st.html("""
<style>
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}
div[data-testid="stVerticalBlock"] > div {
    animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
""")
```

## Gotchas

- Do not use default Plotly themes without zeroing paper and plot background colors; otherwise Streamlit cards look patchy.
- Avoid heavy glowing drop shadows or high-contrast rainbow palettes.
- Always set explicit margins on Plotly figures to maximize real estate inside Streamlit columns.
