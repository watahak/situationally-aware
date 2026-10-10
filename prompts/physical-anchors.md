# Physical Economy Anchors — Energy & Manufacturing

## What This Data Is For

Supports the **Physical & Cash-Flow Anchoring** pillar (CLAUDE.md). The financialization
gap (market cap weight vs GDP share) measures one dimension of distortion. Energy
consumption and manufacturing output are harder-to-fudge physical economy anchors —
they measure what a country actually produces and consumes, independent of financial
market pricing.

The gap is wider than GDP alone suggests. US GDP (~26% of global) is itself
financialized — it includes financial services revenue that inflates the denominator.
Energy and manufacturing strip that out.

**Freshness threshold: 365 days** (annual data, slow-moving).

## Query

Use the following prompt with a web-connected LLM or search tool:

---

Find the most recent available data for:

1. **US share of global primary energy consumption (%)** — source: Energy Institute
   Statistical Review of World Energy (formerly BP Statistical Review), most recent
   edition.

2. **US share of global manufacturing output (%)** — source: World Bank or UNIDO,
   most recent year available.

3. **China share of global primary energy consumption (%)** — same Energy Institute
   source.

4. **China share of global manufacturing output (%)** — same World Bank/UNIDO source.

5. **Europe (EU-27) share of global primary energy consumption (%)** — same Energy
   Institute source.

6. **Europe (EU-27) share of global manufacturing output (%)** — same World Bank/UNIDO
   source.

For each, provide the exact percentage, the source publication, and the data year.

---

## Expected Output Format

Paste results into `contexts/physical-anchors.json` using this structure:

```json
{
  "schema_version": 1,
  "context_type": "structural",
  "data_as_of": "2024",
  "retrieved_on": "2026-10-09",
  "freshness_days": 365,
  "sources": [
    "Energy Institute Statistical Review of World Energy 2025",
    "World Bank / UNIDO 2024"
  ],
  "data": {
    "us_energy_pct": null,
    "us_manufacturing_pct": null,
    "china_energy_pct": null,
    "china_manufacturing_pct": null,
    "europe_energy_pct": null,
    "europe_manufacturing_pct": null,
    "data_year_energy": null,
    "data_year_manufacturing": null,
    "notes": ""
  }
}
```

## Where It Goes

- **analysis/YYYY-MM-macro.md**: Macro Proportionality section — adds physical economy
  dimension. Example: "The US commands 63% of global market cap on 26% of GDP — but
  only ~16% of global energy consumption and ~17% of manufacturing output. The
  financialization premium is wider than GDP alone suggests."
- **analysis/YYYY-MM-vxus-spy.md**: Cash-Flow Anchor section
- Consumed by analyze-macro and analyze-chart skills via the context loading step
