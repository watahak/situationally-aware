---
name: generate-opinion
model: sonnet
effort: medium
description: "Generate a plain-English executive brief from the latest macro analysis — the 'No-BS' version that tells you where money is flowing, why, and what to watch"
---

# Generate Opinion — Executive Brief from Macro Analysis

Reads the latest macro report and distills it into a tight, jargon-free opinion brief with embedded chart directives. Run this AFTER `/analyze-macro` has completed.

## Steps

1. **Load the analytical lens.** Read `references/analytical-lens.md`. Apply the Condensed Lens (Opinion Mode) throughout the opinion brief.

2. Find the latest macro report: look for the most recent `analysis/YYYY-MM-macro.md` file. If none exists, tell the user: *"No macro report found. Run `/analyze-macro` first."*

3. Read the macro report.

4. Generate the opinion brief following the template and writing rules below. Place chart embed directives where they directly support the narrative — 2-4 charts total, chosen dynamically based on what the macro report highlights as most significant.

5. Write to `analysis/YYYY-MM-opinion.md` (same YYYY-MM as the macro report).

6. Run the `humanizer` skill in file mode on the opinion file you just wrote. Preserve all chart directives (`<!-- chart:... -->`), bold signal numbers, and the template section structure.

## Available Chart Embed Directives

Place these HTML comments in the opinion markdown. The Opinion tab in the Streamlit app renders them as real interactive charts from the Signal tab.

| Directive | What it renders |
|---|---|
| `<!-- chart:ratio:SLUG -->` | Ratio spread chart for a pair (e.g., `spy-rsp`, `vxus-spy`, `kweb-qqq`) |
| `<!-- chart:zscore:SLUG -->` | Z-score bar chart for a pair |
| `<!-- chart:heatmap -->` | Momentum ROC heatmap (all ETFs) |
| `<!-- chart:financialization -->` | GDP vs market-cap gap bars by region |
| `<!-- chart:gauges -->` | CTA / dealer gamma / vol-target gauges |
| `<!-- chart:sankey -->` | AI capex circular revenue flow diagram |
| `<!-- chart:butterfly -->` | Physical economy vs financial weight comparison |

Valid pair slugs: `spy-rsp`, `qqq-qqqe`, `vxus-spy`, `ews-eem`, `kweb-mchi`, `kweb-qqq`, `gld-tlt`.

**Usage rules:**
- Place 2-4 charts total — only where they directly support the point being made
- Place the directive on its own line, between markdown sections
- The directive must appear AFTER the text it illustrates, not before
- Choose charts based on what the macro report identifies as the most extreme or important signals

## Output Template

Generate strictly this structure:

```markdown
# The No-BS Brief — [Month Year]

*Generated [date]. Distilled from the [Month Year] macro analysis. This is not financial advice.*

## 🎯 The Core Message

2-3 sentences summarizing the current macro capital flow regime. Clearly state whether capital is crowding, rotating, or fleeing, and name the primary mechanical driver. Bold key numbers.

[Optional: embed the most relevant chart here — e.g., the most extreme ratio or the heatmap]

## 📊 The 3 Big Takeaways

Strictly 3 high-impact, data-backed bullet points. Each combines a quantitative metric with a plain-English explanation of what it reveals about market structure:

1. **[Short label]** — **[metric]**: [what it means in one sentence]
2. **[Short label]** — **[metric]**: [what it means in one sentence]
3. **[Short label]** — **[metric]**: [what it means in one sentence]

[Optional: embed a chart that visualizes the most important takeaway]

## ⚠️ What Could Break?

2-3 specific structural or mechanical catalysts that could unwind the current trend. Focus on:
- Physical drains (energy/CapEx costs)
- Accounting constraints (GAAP depreciation, ASC 606 revenue recognition)
- Systematic positioning flips (CTA momentum reversal, dealer gamma sign change)

Each catalyst: one sentence naming it, one sentence on the mechanism, one sentence on current status from the macro report.

[Optional: embed gauges or butterfly chart if positioning data supports the argument]

## 👁️ What to Actually Watch

3-4 specific ratio thresholds or moving average triggers. For each:
- **[Pair]** at **[level]**: [what a breakdown/breakout signals for portfolio risk]
```

## Writing Rules

- **Jargon Translation.** Use plain-English terms first, technical term parenthesized on first use only. Subsequent uses can use either form.

  | Technical Term | Plain-English Translation |
  |---|---|
  | Dealer Gamma / CTA Percentiles | Automated Fund Momentum |
  | Z-Score Extremes | Stretched Trade / Crowding Level |
  | Financialization Gap | Market Cap Weight vs. Real Economic Output |
  | FCF Yield Disconnect | Cash Return vs. Growth Expectations |

- **Bold signal numbers.** Key ticker pairs and concrete figures in bold throughout (e.g., **0.88% FCF yield**, **+37pp US gap**, **SPY / RSP**). The reader should be able to skim bold text alone and get the story.
- **No financial advice.** "The data shows X" not "you should buy/sell Y."
- **Anti-narrative.** Zero references to news headlines, Fed meetings, earnings, geopolitics, or sell-side research.
- **Tethered to the macro report.** Every claim must cite a specific finding from the macro analysis. No independent analysis, no re-derivation from raw data. If the macro report doesn't support a claim, don't make it.
- **Concise.** The entire opinion should be scannable in under 2 minutes. No filler paragraphs, no redundant context-setting.
- **No dollar signs.** Streamlit renders `$` as LaTeX math delimiters, which garbles inline text. Never use `$` for currency — write amounts as plain numbers with units (e.g., **250B/yr**, **75B**, **4.5%**). If a dollar sign is truly needed, escape it as `\$`.
