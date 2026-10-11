---
name: analyze-macro
model: sonnet
effort: medium
description: "Monthly macro analysis — generates per-chart deep dives with dynamic structural risk identification, then synthesizes with cross-referencing, valuation territory map, and proportionality assessment"
---

# Analyze Macro — Monthly Report Generator

One extraction, one LLM pass, all output files generated. This is the monthly publishing skill.

## Steps

1. **Load the analytical lens.** Read `references/analytical-lens.md`. Apply the Detailed Lens (Data Analysis Mode) throughout all analysis. Use the Context type handling rules and Context integration map from that file when loading external contexts in step 4.

2. Run the extraction script with archive flag:
   ```
   .venv/bin/python scripts/extract_data.py -o $TMPDIR/mini-quant-data.json --archive
   ```
   This saves the JSON to both `$TMPDIR` (for reading) and `analysis/YYYY-MM-data.json` (for version history).

3. Read the JSON output from `$TMPDIR/mini-quant-data.json`.

4. **Load external contexts.** Check for `contexts/*.json` files. For each file found:
   - Read it and parse the JSON envelope (`schema_version`, `context_type`, `data_as_of`, `retrieved_on`, `freshness_days`, `sources`, `data`).
   - Skip files where `data_as_of` is null (empty template, not yet populated).
   - Compute staleness: `today - retrieved_on` in days vs `freshness_days`.
   - If **fresh** (within threshold): weave the data into the relevant analysis sections per the context integration map from the analytical lens (step 1).
   - If **stale** (over threshold): include the data but flag it: *"[Data source] last updated [retrieved_on] — may be stale, verify before acting."*
   - If **missing** (file doesn't exist): note the gap honestly: *"[Metric] not available — see prompts/[file] to retrieve."*

   Apply the context type handling rules and integration map from the analytical lens loaded in step 1.

5. **FLAG**: Before generating analysis, show the user a compact summary table of the extracted data:

   | Pair | Current | 6M Chg | Z-Score | vs 50-SMA | vs 200-SMA | Percentile |
   |------|---------|--------|---------|-----------|------------|------------|

   Wait for the user to confirm the data looks correct before proceeding.

6. Generate ALL output files. Write them in this order:
   - Per-chart deep dives: `analysis/YYYY-MM-{pair-slug}.md` for each ratio pair
   - Macro synthesis: `analysis/YYYY-MM-macro.md`

   Use the current year-month for YYYY-MM. Pair slugs: lowercase, spaces and slashes become hyphens (`SPY / RSP` → `spy-rsp`).

---

## Per-Chart Deep Dive Framework

Generate one file per ratio pair. Each should be readable in 2 minutes.

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

Examine the data for this pair through each analytical lens. Derive risks from what the numbers show — do NOT recite generic examples.

**1. MECHANICAL — What structural force could produce this ratio movement?**
- What does this pair's index construction mechanically do when price rises/falls?
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
- If at an extreme low: is capital structurally fleeing, or temporary dislocation?
- If at an extreme high: is everyone on the same side? What's the reversion catalyst?
- Use: Z-score extremes, days in extreme territory, direction, both legs' absolute returns

Name each identified risk with a short descriptive label. If no structural risk is identifiable from the data for a given lens, say so.

## Risk–Price Proportionality

**Assessment: [Proportionate / Understated / Overstated]**

Given the structural risks identified above and the observed data (6M delta, Z-score, percentile, both legs' absolute returns):
- **Proportionate**: price delta roughly reflects the mechanical forces at work
- **Understated**: structural risks are larger than the price movement suggests
- **Overstated**: price has moved beyond what structural data justifies

One sentence explaining the call.

## Valuation Territory

**[Territory Label]**

Derive mechanically:
- **Extreme Premium**: Z-score > +2 AND percentile > 90th (AND financialization gap > +20pp where available)
- **Premium**: Z-score +1 to +2 OR percentile 75th–90th
- **Fair Value**: Z-score -1 to +1 AND percentile 25th–75th
- **Discount**: Z-score -1 to -2 OR percentile 10th–25th (apply Value Trap check)
- **Deep Discount**: Z-score < -2 AND percentile < 10th (must distinguish: value trap or genuine dislocation)

Context:
- Concentration pairs (SPY/RSP, QQQ/QQQE): territory = concentration premium/discount
- Geographic pairs (VT/SPY, EWS/EEM, KWEB/MCHI, KWEB/QQQ): territory = relative regional valuation
- GLD/TLT: territory = hard-money vs fiat-duration positioning (no GDP anchor)

One sentence: what this territory means for the specific thing this pair measures.

## What to Watch
- 1-2 specific trigger levels that would change the picture
```

---

## Macro Synthesis Framework

This file ties everything together. Write it AFTER all per-chart deep dives are done — the macro synthesis references and cross-references the per-chart findings. Readable in 5 minutes.

```markdown
# Macro Capital Flow Report — [Month Year]

*Generated [date]. Data as of market close [date]. 6-month lookback.*

*This report analyzes relative price ratios, momentum, and structural signals across global asset classes. It is not financial advice.*

## Executive Summary
2-3 sentences a retail investor can immediately understand. No jargon. Include the dominant capital flow direction, the most extreme signal, and the overall valuation territory lean.

## Capital Flow Map
Synthesize all ratios into a directional picture:
- **US vs World** (VT/SPY): capital flowing toward or away from the US?
- **Concentrated vs Broad** (SPY/RSP, QQQ/QQQE): mega-cap concentration or breadth improvement?
- **Risk Appetite** (EWS/EEM): defensive or risk-seeking EM capital?
- **China Tech vs Broad / vs US** (KWEB/MCHI, KWEB/QQQ): Chinese tech gaining or losing ground?
- **Real vs Fiat** (GLD/TLT): hard assets or government bonds?

Include a simple ASCII flow diagram showing where capital is moving.

## Regime Assessment
Characterize the current regime:
- Risk-On Broad / Risk-On Concentrated / Risk-Off Defensive / Rotation / Compression
- State which regime and the 2-3 data points that support it

## Cross-Reference Patterns

After reviewing all pairs, answer these questions:
1. **Convergence**: How many pairs confirm the dominant capital flow direction? Name them.
2. **The Outlier**: Which pair is telling a different story? What does the outlier reveal about a secondary force?
3. **Secondary Theme**: Remove the dominant theme — what pattern emerges from the remaining pairs?
4. **Contradictions**: Are any pairs sending contradictory signals? (e.g., US concentration rising AND safe havens rising would be unusual — investigate)
5. **Reinforcing Loops**: Do any pairs' structural risks amplify each other? (e.g., SPY/RSP concentration + VT/SPY falling = the same mega-cap gravity pulling both)

## Valuation Territory Map

| Sector/Pair | Territory | Key Structural Risk | Proportionate? |
|---|---|---|---|
| US Mega-Cap (SPY/RSP) | [from per-chart] | [from per-chart] | [from per-chart] |
| US Tech (QQQ/QQQE) | [from per-chart] | [from per-chart] | [from per-chart] |
| Global vs US (VT/SPY) | [from per-chart] | [from per-chart] | [from per-chart] |
| EM Quality (EWS/EEM) | [from per-chart] | [from per-chart] | [from per-chart] |
| China Tech/Broad (KWEB/MCHI) | [from per-chart] | [from per-chart] | [from per-chart] |
| China/US Tech (KWEB/QQQ) | [from per-chart] | [from per-chart] | [from per-chart] |
| Safe Haven (GLD/TLT) | [from per-chart] | [from per-chart] | [from per-chart] |

## Macro Proportionality

Zoom out from individual pairs. Across ALL pairs:
- Is the overall market positioning (regime + territory distribution) proportionate to the structural backdrop?
- Count: how many pairs are at Premium or Extreme Premium? How many at Discount or Deep Discount?
- Does the financialization gap data support this distribution, or does price-level positioning outrun real economic fundamentals?
- One paragraph assessment: is the market as a whole priced proportionately, or is there a systematic lean toward narrative-driven positioning?

## Structural Flags

Consolidate the most important structural risks from across all per-chart analyses. Do NOT repeat every risk — surface only the ones that:
1. Appear in multiple pairs (reinforcing loop)
2. Are at extreme levels (Z-score beyond ±2)
3. Have a disproportionate risk-price mismatch (understated or overstated)

For each flag: name it, state the evidence, and note whether it's proportionately priced.

Additional flag sources:
4. If TIP heatmap data is present, use TIP vs TLT ROC divergence to diagnose the mechanism behind safe haven moves. TIP holding while TLT falls = real-rate repricing (Fed policy driven). Both falling = duration rejection (structural, not rate-driven). Note the diagnosis in the Safe Haven structural flag.
5. If `contexts/systematic-positioning.json` is loaded and fresh, add a "Systematic Positioning" flag when readings are extreme (e.g., CTAs max-long + negative dealer gamma = trend mechanically reinforced but vulnerable to reversal on volatility spike).

## Structural Persistence & Correction Mechanics

Bridge between Structural Flags and positioning. One opening paragraph: cap-weighted reflexivity is self-reinforcing on both sides (bubble inflates via passive inflows, depression deepens via forced rebalancing). Both are non-fundamental — they persist until a breaker fires.

### Depression-Side Correction
For each: one-sentence definition + *Current status* from this month's data.
1. **Cash Flow Buyback Trap** — suppressed price spikes FCF yield; buybacks shrink float faster than institutions sell
2. **Seller Inventory Depletion** — allocation approaches zero → no supply left to sell
3. **Capital Ownership Transfer** — domestic/non-aligned capital buys the yield gap Western mandates refuse
4. **Arbitrage Prisoner's Dilemma** — extreme earnings yield spread incentivizes defection from consensus
5. **Permanent only if** — expropriation, nationalization, or asset freeze. Otherwise, cash flow = gravity.

### Bubble-Side Breakers
Same format:
1. **Symmetrical Outflow Cascade** — passive sells proportional to index weight, concentrating losses in heaviest names
2. **Earnings Yield vs Risk-Free Squeeze** — equity yield below risk-free → active capital sells into passive bid
3. **AI Capex ROI Disconnect** — capex without proportional returns shrinks FCF, removes buyback support
4. **Corporate Supply Expansion** — SBC, issuance, insider selling dilute passive inflows
5. **Index Caps / Regulation** — special rebalances at concentration thresholds, antitrust at GDP-gap extremes

### Mechanism Status
Table: `| Mechanism | Status | Active? |` — one row per mechanism. One-line net assessment comparing depression-side advancement vs bubble-side readiness.

## Retail Investor Watchlist

**Most important section.** 2-4 plain-English items. For each:
- One sentence: what to watch
- One sentence: why it matters (reference the structural risk, not a narrative)
- One sentence: what would change the picture
- Include the valuation territory so readers know where things stand

## Positioning Principles

*Not financial advice.* One sentence: position-sizing environment vs conviction environment, based on whether mechanics and fundamentals agree or conflict.

**Asymmetry table**: `| Scenario | If right | If wrong | Pain type | Duration |` — three rows (follow trend, go contrarian, sit in cash). One sentence after: most retail investors exit on pain threshold, not price target.

**4 principles** — one sentence each, derived from Mechanism Status and Structural Flags:
1. Ride the direction, but size for the FCF floor if mechanics reverse
2. Structural cheapness without a visible trigger is a value trap
3. When all pairs agree, the unwind is correlated — size accordingly
4. Watch mechanical gauges (name specific current readings), not headlines

**One closing sentence**: concrete behavioral rule tied to current systematic positioning.

## Chart Detail

[Include the per-chart deep dive content for each pair — Current State, 6-Month Trend, Structural Risk Identification, Risk-Price Proportionality, Valuation Territory, What to Watch. This is summary form — 3-5 bullets per section, reference the standalone files for full detail.]

## Data Appendix

| Pair | Current | 6M Chg | Z-Score | vs 50-SMA | vs 200-SMA | 6M Percentile | Territory |
|------|---------|--------|---------|-----------|------------|---------------|-----------|
| ...  | ...     | ...    | ...     | ...       | ...        | ...           | ...       |
```

---

## Writing Rules (apply to ALL output files)

- **No financial advice.** "The data shows X" not "you should buy/sell Y"
- **Anti-narrative.** Zero references to news headlines, Fed meetings, earnings, geopolitics, or sell-side research. Only what the ratios and structural data show
- **Plain English first.** Lead every point with a sentence anyone can understand
- **Structural over speculative.** Explain mechanics (passive flows, index rules, mean reversion), not predictions
- **Dynamic risks only.** Every structural risk must be derived from the current data. Never copy risks from prior reports — re-derive them fresh each month
- **Concise.** 3-5 bullets per section. Scannable with headers
- **Honest about limitations.** If the data doesn't clearly point to a risk, say so. If a territory call is borderline, say which direction it leans and why
