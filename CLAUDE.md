# mini-quant

Macro-quant analysis toolkit with Streamlit dashboard. Tracks relative spread ratio pairs, rolling Z-score extremes, and structural capital flow signals.

## Project structure

```
app.py                  Streamlit entry point
core.py                 Shared calculations (ROC, ratio, Z-score, financialization gap)
settings/market.py      CONFIG: ratio pairs, tickers, Z-score params, macro anchors
ui/                     Streamlit UI modules (tabs, charts, theme)
scripts/
  extract_data.py       Fetches yfinance data, computes metrics, outputs JSON
  validate_contexts.py  Checks context JSON freshness and schema validity
analysis/               Monthly output: data JSON, per-pair MDs, macro MD, opinion MD
prompts/                Markdown queries for human-operated web-connected LLM data retrieval
contexts/               Structured JSON output of those prompts
references/             Shared reference documents (analytical lens)
.claude/skills/         Claude Code skills for analysis and generation
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Key workflows

- **Monthly analysis:** run `/analyze-macro` — extracts market data, loads contexts, generates per-chart deep dives + macro synthesis report
- **Executive brief:** run `/generate-opinion` after macro analysis is complete
- **Context refresh:** paste prompts from `prompts/*.md` into a web-connected LLM (e.g. Gemini), paste structured results into corresponding `contexts/*.json`
- **Freshness check:** run `scripts/validate_contexts.py` to see which contexts need refreshing

## Adding a new ratio pair

1. Add to `CONFIG["ratio_pairs"]` in `settings/market.py` (name, numerator, denominator, tooltip)
2. Add to `CONFIG["zscore_pairs"]` if Z-score tracking is desired
3. Add numerator/denominator tickers to the appropriate category list (`us_concentration`, `global_geographic`, `safe_havens`)
4. Add both tickers to `CONFIG["heatmap_tickers"]`

## Prompts → contexts → analysis pipeline

Each `prompts/*.md` describes a query and its expected JSON schema. The human runs the query externally and pastes structured output into the corresponding `contexts/*.json`. Each context JSON has an envelope with `schema_version`, `context_type`, `data_as_of`, `retrieved_on`, `freshness_days`, `sources`, and `data`. The analyze-macro skill loads these contexts, checks freshness against `freshness_days`, and weaves them into the analysis. The three context types (`structural`, `seasonal`, `tactical`) have different freshness thresholds and presentation rules — see `references/analytical-lens.md` for details.

## Dependencies

Python 3.14. Key packages: streamlit, plotly, yfinance, pandas. Full list in `requirements.txt`.
