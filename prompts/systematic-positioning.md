# Systematic Strategy Positioning Data

## What This Data Is For

Supports the **Mechanical & Structural Awareness** pillar (CLAUDE.md). The dashboard
tracks price ratios and Z-scores, but cannot observe the positioning of systematic
strategies (CTAs, vol-targeting, risk parity) that mechanically amplify or dampen
trends. Knowing whether these strategies are max-long or deleveraging provides context
for interpreting Z-score extremes and potential reversal triggers.

This is the most perishable data type — systematic positioning changes weekly.

**Freshness threshold: 14 days.**

## Query

Use the following prompt with a web-connected LLM or search tool:

---

Find the most recent available data on systematic strategy positioning in US equities:

1. **CTA/trend-following aggregate positioning in US equities**: net long or short,
   and historical percentile if available. Sources: Deutsche Bank CTA positioning
   index, Societe Generale CTA index, or Goldman Sachs systematic strategy monitor.
   If primary sources are paywalled, check for recent summaries in financial media
   (Bloomberg, FT, or macro commentary that cites these sources).

2. **Dealer gamma exposure on SPY and QQQ options**: is aggregate dealer gamma
   positive (stabilizing — dealers buy dips, sell rips) or negative (destabilizing —
   dealers amplify moves)? Approximate magnitude relative to recent history.
   Sources: SpotGamma, SqueezeMetrics GEX, or similar options flow analytics.

3. **Systematic strategy concentration signals**: are vol-targeting and risk-parity
   strategies at max equity allocation (low vol environment) or deleveraging?
   Sources: Nomura systematic strategy monitor, JPM vol-targeting estimate, or
   similar.

Provide directional readings (long/short, positive/negative, max/reduced), rough
magnitude or percentile where available, and source with date.

---

## Expected Output Format

Paste results into `contexts/systematic-positioning.json` using this structure:

```json
{
  "schema_version": 1,
  "context_type": "tactical",
  "data_as_of": "2026-10-07",
  "retrieved_on": "2026-10-09",
  "freshness_days": 14,
  "sources": [
    "Deutsche Bank CTA Positioning Index via Bloomberg",
    "SpotGamma GEX Dashboard"
  ],
  "data": {
    "cta_us_equity_position": null,
    "cta_percentile": null,
    "dealer_gamma_spy": null,
    "dealer_gamma_qqq": null,
    "gamma_magnitude": null,
    "vol_target_equity_alloc": null,
    "notes": ""
  }
}
```

Field values:
- `cta_us_equity_position`: "max long" / "net long" / "neutral" / "net short" / "max short"
- `cta_percentile`: 0-100 (historical percentile) or null if unavailable
- `dealer_gamma_spy` / `dealer_gamma_qqq`: "positive" / "negative" / null
- `gamma_magnitude`: free text describing magnitude vs recent history
- `vol_target_equity_alloc`: "max" / "elevated" / "neutral" / "reduced" / "minimum"

## Where It Goes

- **analysis/YYYY-MM-macro.md**: Structural Flags section — adds a "Systematic
  Positioning" flag when readings are extreme. Example: "CTAs at 95th percentile
  net long + negative dealer gamma = trend is mechanically reinforced but vulnerable
  to sharp reversal if volatility spikes."
- **analysis/YYYY-MM-spy-rsp.md** and **qqq-qqqe.md**: Mechanical lens — systematic
  positioning context for concentration pairs
- Consumed by analyze-macro and analyze-chart skills via the context loading step
