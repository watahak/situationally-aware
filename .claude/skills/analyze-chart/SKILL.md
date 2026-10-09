---
name: analyze-chart
model: sonnet
effort: medium
description: "Ad-hoc deep dive on a single ratio pair — dynamic structural risk identification, proportionality assessment, and valuation territory call"
---

# Analyze Chart — Single Pair Deep Dive

Ad-hoc analysis of one ratio pair. Use between monthly `analyze-macro` runs for a fresh read on a specific chart.

## Analytical Lens (apply throughout — from CLAUDE.md)

Before writing anything, run every data point through these filters:

| Pillar | Action |
|---|---|
| **Anti-Narrative Skepticism** | Never explain a ratio movement with a headline or event. Ask: "What mechanical force explains this?" If none is visible in the data, say so honestly — do not fill the gap with speculation. |
| **Mechanical & Structural Awareness** | Identify the index construction rule or capital flow mechanic that could produce this movement. Think: cap-weighting feedback loops, passive rebalancing, systematic VaR/CTA triggers, options gamma, forced 401(k) inflows. |
| **Physical & Cash-Flow Anchoring** | Compare price movements to financialization gap data (where available). Ask: "Is this price justified by real economic output, or is it financialization premium?" For concentration pairs, ask: "Is revenue growth anchored in end-user demand, or is it circular vendor financing?" When FCF yield data is available in the JSON (`fundamentals` section), use it to anchor concentration pair assessments — compare the aggregate Mag 7 FCF yield against the QQQ/QQQE concentration premium to test whether price gains are backed by real cash generation. When TIP heatmap data is available, use it to diagnose safe haven behavior: if TLT falls while TIP holds, the move is real-rate driven; if both TLT and TIP fall, it is duration rejection. When external context files are loaded (see step 2b), use physical economy anchors and circular revenue data where relevant. |
| **Systematic Self-Defense** | For every extreme reading, explicitly classify: **value trap** (structural capital flight making something look "cheap") or **crowded trade** (momentum at extremes with everyone on the same side). State which and why. |

---

## Steps

1. Determine which pair from the user's argument (e.g., `analyze-chart SPY / RSP`). If no argument, ask. Valid pairs come from `core.py` CONFIG `ratio_pairs`.

2. Run the extraction script:
   ```
   .venv/bin/python scripts/extract_data.py -o $TMPDIR/mini-quant-data.json
   ```

3. Read the JSON, focus on the specified pair in `ratio_pairs`, `zscores`, `heatmap`, and `financialization`.

4. **Load external contexts.** Check for `contexts/*.json` files relevant to this pair:
   - For QQQ/QQQE or SPY/RSP: load `contexts/mag7-circular-revenue.json` if it exists.
   - For VXUS/SPY or geographic pairs: load `contexts/physical-anchors.json` if it exists.
   - For GLD/TLT: TIP heatmap data is already in the JSON (no context file needed).
   - For any pair: load `contexts/systematic-positioning.json` if it exists (mechanical lens context).
   - Skip files where `data_as_of` is null (empty template, not yet populated).
   - Apply freshness check: `today - retrieved_on` vs `freshness_days`. If stale, flag it. If missing, note the gap.
   - Apply context type framing: `"structural"` = permanent anchor, present as baseline fact. `"seasonal"` = earnings-cycle risk, highlight during earnings window, label *"Seasonal structural risk"*. `"tactical"` = fast-moving, always show data date, label *"Tactical — as of [date]"*.

5. Generate analysis using the framework below and write to `analysis/YYYY-MM-{pair-slug}.md`.
   Pair slug: lowercase, spaces and slashes become hyphens (`SPY / RSP` → `spy-rsp`).

---

## Output Framework

```markdown
# [Pair Name] — Deep Dive — [Month Year]

*Generated [date]. Data as of [most recent trading day].*

> **One-sentence summary**: [plain English — what this ratio is telling us right now]

## Current State
- Current ratio value and plain-English meaning (use the pair's tooltip as guide)
- Position vs 50-SMA and 200-SMA (above both = strong trend, between = transitional, below both = weak)
- Whether 50-SMA is above or below 200-SMA (structural trend direction)
- Z-score reading: |Z| < 1 = normal, 1-2 = elevated, > 2 = extreme
- Where it sits in the 6M range (percentile)

## 6-Month Trend
- Direction and magnitude (change_6m_pct)
- Monthly trajectory: describe the path using monthly_values (steady decline? V-shape? round-trip?)
- SMA regime: is 50-SMA above 200-SMA? Any crossovers?
- Z-score behavior: days in extreme territory, direction (rising/falling/sideways), range

## Structural Risk Identification

Examine the data for this pair through each analytical lens. Do NOT recite generic risks — derive them from what the numbers actually show.

**1. MECHANICAL — What structural force could produce this ratio movement?**
- What does this pair's index construction mechanically do when price rises/falls? (e.g., cap-weighted index buys more of winners → feedback loop)
- Is the movement self-reinforcing through passive flow mechanics?
- Are there forced buyers or sellers (rebalancing, 401(k) auto-allocation, systematic strategies)?
- Use: ratio direction, SMA positioning, percentile, Z-score extremes

**2. CASH-FLOW ANCHOR — Is this price anchored in reality?**
- Check the financialization data: does the pair's region have a market-cap-to-GDP gap? How large?
- For concentration pairs: are the top holdings of the numerator ETF each other's customers/vendors? If so, how much "growth" is circular revenue vs new end-user demand?
- For concentration pairs (SPY/RSP, QQQ/QQQE): if `fundamentals` data is present in the JSON, reference the aggregate Mag 7 FCF yield (both simple average and market-cap-weighted). A declining FCF yield alongside rising concentration ratios strengthens the "circular revenue" risk flag. If `contexts/mag7-circular-revenue.json` is loaded, cite specific inter-company revenue figures.
- For geographic pairs: does the price premium/discount reflect actual economic output share? If `contexts/physical-anchors.json` is loaded, compare market cap weight against energy consumption and manufacturing output shares — not just GDP.
- Use: financialization gap data, heatmap ROC (is the underlying ETF's absolute return justified?), fundamentals data, external contexts

**3. SELF-DEFENSE — Value trap or crowded trade?**
- If the ratio is at an extreme low (potential "cheap" entry): is capital structurally fleeing this side, or is it a temporary dislocation? What would need to change for the flow to reverse?
- If the ratio is at an extreme high (potential "expensive"): is everyone on the same side of this trade? What's the reversion catalyst?
- For GLD/TLT: if TIP heatmap data is present, use TIP vs TLT ROC to distinguish real-rate repricing from duration rejection. This diagnoses the mechanism, not just the direction.
- Use: Z-score extremes, days in extreme territory, direction, both legs' absolute returns from heatmap

Name each identified risk with a short descriptive label. If no structural risk is identifiable from the data for a given lens, say so — don't fabricate one.

## Risk–Price Proportionality

**Assessment: [Proportionate / Understated / Overstated]**

Given the structural risks identified above and the observed data:
- 6M price delta: [change_6m_pct]%
- Z-score: [current] (normal / elevated / extreme)
- Percentile: [percentile_6m]th
- Both legs' absolute performance: [numerator ROC] vs [denominator ROC]

Is the price movement proportionate to the structural risks?
- **Proportionate**: price delta roughly reflects the mechanical forces at work
- **Understated**: structural risks are larger than the price movement suggests — market may be complacent
- **Overstated**: price has moved beyond what structural data justifies — likely momentum/narrative overshoot

One sentence explaining the call.

## Valuation Territory

**[Territory Label]**

Derive the territory mechanically from the data:
- **Extreme Premium**: Z-score > +2 AND percentile > 90th (AND financialization gap > +20pp where available)
- **Premium**: Z-score +1 to +2 OR percentile 75th–90th
- **Fair Value**: Z-score -1 to +1 AND percentile 25th–75th
- **Discount**: Z-score -1 to -2 OR percentile 10th–25th (apply Value Trap check)
- **Deep Discount**: Z-score < -2 AND percentile < 10th (must distinguish: value trap or genuine dislocation)

Context for interpretation:
- Concentration pairs (SPY/RSP, QQQ/QQQE): territory = concentration premium/discount, not geographic valuation
- Geographic pairs (VT/SPY, EWS/EEM, KWEB/MCHI, KWEB/QQQ): territory = relative regional valuation
- GLD/TLT: territory = hard-money vs fiat-duration positioning (no GDP anchor — use Z-score + percentile + SMA only)

One sentence: what this territory means for the specific thing this pair measures.

## What to Watch
- 1-2 specific trigger levels (SMA levels, Z-score thresholds, percentile boundaries) that would change the picture
- What structural shift would move this to the next territory?
```

---

## Writing Rules
- **No financial advice** — "the data shows X" not "you should buy/sell"
- **Anti-narrative** — zero references to news, headlines, earnings, Fed meetings, or geopolitics. Only what the ratios and metrics show
- **Plain English first** — lead every point with a sentence a non-expert can understand, then add technical detail
- **Structural over speculative** — explain mechanics, not predictions
- **Concise** — 3-5 bullets per section max. Scannable headers
- **Honest about limitations** — if the data doesn't clearly point to a risk, say so
