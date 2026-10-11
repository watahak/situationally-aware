# Capital Structure Decoder

A Streamlit dashboard that decodes market structure through ratio spreads, rolling Z-scores, and physical anchors — tracking where systematic engines (passive flows, CTA triggers, index mechanics) are forcing capital, instead of chasing headlines.

## What it does

**Signal tab** — three analytical lenses on ETF price data from Yahoo Finance:

- **What's Moving** — Rate-of-change heatmap across tactical (1W–1M), cyclical (3M–6M), and structural (1Y–5Y) horizons. Identifies where systematic engines are forcing capital across time frames.

- **Where Is Leadership Shifting** — Ratio spreads with 50/200-day SMA overlays and 60-day rolling Z-scores for seven ETF pairs. Z-scores beyond ±2σ flag statistically crowded or stretched positions. Pairs tracked:

  | Pair | What it measures |
  |---|---|
  | SPY / RSP | US large-cap concentration (cap-weight vs equal-weight) |
  | QQQ / QQQE | Nasdaq 100 tech mega-cap concentration |
  | VXUS / SPY | International vs US equity leadership |
  | EWS / EEM | Singapore vs broad emerging markets |
  | KWEB / MCHI | Chinese internet vs broad China |
  | KWEB / QQQ | China tech vs US tech |
  | GLD / TLT | Gold vs long-duration Treasuries |

- **Is It Justified** — Financialization gap chart comparing each region's share of global market cap against its share of global GDP. Flags where capital markets price beyond real economic output.

**Opinion tab** — renders the executive brief from `/generate-opinion` with embedded live charts, plus a "Full Macro Analysis Report" expander with the `/analyze-macro` output.

## Setup

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```
streamlit run app.py
```

## Project structure

```
app.py              Streamlit UI, chart builders, layout
core.py             Config, pair definitions, calc functions (ROC, ratio, Z-score, rotation)
requirements.txt    streamlit, plotly, yfinance, pandas
analysis/           Monthly macro and per-pair analysis reports (markdown)
contexts/           Reference data for analysis prompts
prompts/            Prompt templates for analysis generation
scripts/            Data extraction utilities
```

## Data

All price data is fetched via `yfinance` and cached for 12 hours. Macro anchors (GDP shares, market cap weights) are manually maintained in `core.py` — update `MACRO_ANCHORS` with the latest IMF WEO / MSCI ACWI data periodically.
