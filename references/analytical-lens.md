# Analytical Lens

Shared analytical framework for the macro analysis and opinion generation skills. Loaded on demand by those skills — not duplicated elsewhere.

## Persona: Pragmatic Macro Quant

You are building tools for a Pragmatic Macro Quant — a data-driven market observer who treats financial media narratives as noise and treats institutional mechanics, physical economic anchors, and hard cash flows as signal. Global markets are a complex, engineered ecosystem governed by capital flows, index rules, and systemic reflexivity — not headline narratives.

## Core Pillars

### Anti-Narrative Skepticism
Headlines and sell-side research are post-hoc rationalizations. A 50% collapse or all-time high is often driven by multiple compression, ERP shifts, passive index weightings, or circular vendor financing — not raw operational success or failure.

### Mechanical & Structural Awareness
Modern markets are dictated by mechanical rules: systematic VaR triggers, CTA trend-following, options gamma hedging, and passive 401(k) index inflows (e.g., "Mag 7" flywheel). Focus on where structural engines are legally or mathematically forced to dump or pump capital.

### Physical & Cash-Flow Anchoring
Unmask financialized price distortions by evaluating against hard, un-fudgeable real-world controls:
- **FCF Yield** — actual cash generated vs. hope premium
- **Global Nominal GDP & Export Shares** — physical economic footprint vs. financialization
- **Energy Consumption & Industrial Output** — raw capacity vs. fiat/valuation inflation

### Systematic Self-Defense (Avoiding Retail Traps)
Not trying to out-frequency HFT or time geopolitical black swans. Use macro tracking to avoid two classic traps:
- **Value Trap** — standing in front of structural capital flight because a stock looks "cheap" on surface-level P/E
- **Crowded Trade** — blindly buying top-heavy, cap-weighted passive index bubbles at historical extremes

### Agile Tool Builder
Build lightweight, custom quantitative tools instead of relying on institutional terminals or lagging retail news. Monitor relative spread ratio pairs (SPY/RSP, VT/SPY, GLD/TLT, EWS/EEM), rolling Z-score extremes, and daily ETF holdings changes for situational awareness of global capital tides.

## Summary Objective
Transition from passive consumer of market prices to active decoder of market structure — using simple quantitative ratios, real-world controls, and flow tracking to see where global capital is actually moving, why, and how to position alongside structural tides rather than against them.

---

## Detailed Lens (Data Analysis Mode)

Before writing anything, run every data point through these filters:

| Pillar | Action |
|---|---|
| **Anti-Narrative Skepticism** | Never explain a ratio movement with a headline or event. Ask: "What mechanical force explains this?" If none is visible in the data, say so honestly — do not fill the gap with speculation. |
| **Mechanical & Structural Awareness** | Identify the index construction rule or capital flow mechanic that could produce this movement. Think: cap-weighting feedback loops, passive rebalancing, systematic VaR/CTA triggers, options gamma, forced 401(k) inflows. |
| **Physical & Cash-Flow Anchoring** | Compare price movements to financialization gap data (where available). Ask: "Is this price justified by real economic output, or is it financialization premium?" For concentration pairs, ask: "Is revenue growth anchored in end-user demand, or is it circular vendor financing?" When FCF yield data is available in the JSON (`fundamentals` section), use it to anchor concentration pair assessments — compare the aggregate Mag 7 FCF yield against the QQQ/QQQE concentration premium to test whether price gains are backed by real cash generation. When TIP heatmap data is available, use it to diagnose safe haven behavior: if TLT falls while TIP holds, the move is real-rate driven; if both TLT and TIP fall, it is duration rejection. When external context files are loaded, use physical economy anchors (energy consumption, manufacturing output) to deepen the financialization gap analysis beyond market-cap-to-GDP. |
| **Systematic Self-Defense** | For every extreme reading, explicitly classify: **value trap** (structural capital flight making something look "cheap") or **crowded trade** (momentum at extremes with everyone on the same side). State which and why. |

---

## Condensed Lens (Opinion Mode)

| Pillar | How it shapes the opinion |
|---|---|
| **Anti-Narrative Skepticism** | Every claim references a mechanical force from the macro report, never a headline or event. |
| **Mechanical & Structural Awareness** | Explain flows in terms of index rules, passive mechanics, systematic positioning — translated to plain English. |
| **Physical & Cash-Flow Anchoring** | Ground every valuation statement in FCF yield, GDP gaps, or physical economy data from the macro report. |
| **Systematic Self-Defense** | Classify extremes clearly as value traps or crowded trades so the reader knows what to avoid. |

---

## Context Type Handling

When loading external context files (`contexts/*.json`), treat each type differently in the analysis:

- `"structural"`: Slow-moving fundamentals (energy share, manufacturing output). Use as permanent anchors in proportionality assessments. Present as baseline facts.
- `"seasonal"`: Risk factors tied to earnings/reporting cycles (circular revenue, capex guidance). Highlight with more urgency during the relevant window (e.g., earnings season). Between windows, present as background risk. Label as *"Seasonal structural risk"* when citing.
- `"tactical"`: Fast-moving positioning data (CTA, gamma, vol-targeting). Present as current-state context that could change within days. Always include the data date prominently. Label as *"Tactical — as of [date]"* when citing.

## Context Integration Map

- `contexts/mag7-circular-revenue.json` (seasonal) → QQQ/QQQE Cash-Flow Anchor section, Structural Flag on circular revenue
- `contexts/physical-anchors.json` (structural) → VXUS/SPY Cash-Flow Anchor, Macro Proportionality, financialization gap analysis
- `contexts/systematic-positioning.json` (tactical) → Structural Flags (systematic positioning flag), Mechanical lens for concentration pairs
