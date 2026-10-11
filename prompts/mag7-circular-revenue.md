# Mag 7 Circular Revenue & AI Capex Data

## What This Data Is For

Supports the **Physical & Cash-Flow Anchoring** pillar (CLAUDE.md). The QQQ/QQQE
concentration pair analysis flags "circular revenue risk" — Mag 7 companies sell AI
infrastructure to each other, inflating top-line growth without proportionate new
end-user demand. This query gathers the numbers to quantify that claim instead of
asserting it without evidence.

**Freshness threshold: 90 days** (quarterly earnings cadence).

## Query

Use the following prompt with a web-connected LLM or search tool:

---

Find the following data points for the "Magnificent 7" stocks (Apple, Microsoft,
NVIDIA, Alphabet, Amazon, Meta, Tesla) using the most recent quarterly earnings
(10-Q or earnings release):

1. **Combined annual AI/cloud capex** for MSFT, GOOG, AMZN, META (the four
   hyperscalers). Use the most recent quarter's capex annualized if full-year
   data is not yet available. Source: earnings releases or 10-Q filings.
   **Also provide the per-company breakdown** (annualized capex in $B for each).

2. **NVIDIA data center revenue breakdown**: what percentage of NVIDIA's data
   center revenue comes from the four hyperscalers above? Source: NVIDIA earnings
   call transcripts, sell-side estimates, or SEC filings.

3. **Inter-company revenue estimate**: of the combined Mag 7 revenue (TTM), what
   percentage is estimated to come from sales to other Mag 7 members? Include:
   - AI chip/hardware sales (NVIDIA to hyperscalers) — estimate in $B
   - Cloud services sold between members (Azure, GCP, AWS) — estimate in $B
   - Advertising spend between members — estimate in $B
   Provide a rough lower-bound estimate with sourcing. **Also provide the $B
   breakdown** for each category (used for `intercompany_breakdown_bn`).

4. **Combined Mag 7 total revenue (TTM)** for denominator context.

Return as structured data points with sources and dates.

---

## Expected Output Format

Paste results into `contexts/mag7-circular-revenue.json` using this structure:

```json
{
  "schema_version": 1,
  "context_type": "seasonal",
  "data_as_of": "2026-Q3",
  "retrieved_on": "2026-10-09",
  "freshness_days": 90,
  "sources": [
    "NVDA 10-Q FY2027 Q2",
    "MSFT earnings release FY2027 Q1"
  ],
  "data": {
    "hyperscaler_ai_capex_annual_bn": null,
    "nvidia_dc_rev_hyperscaler_pct": null,
    "mag7_intercompany_rev_pct": null,
    "mag7_total_rev_ttm_bn": null,
    "capex_by_company": {"MSFT": null, "AMZN": null, "GOOGL": null, "META": null},
    "intercompany_breakdown_bn": {"ai_hardware": null, "cloud_compute": null, "digital_ads": null},
    "notes": ""
  }
}
```

## Where It Goes

- **analysis/YYYY-MM-macro.md**: Structural Flag on circular revenue + QQQ/QQQE Chart Detail — cite specific numbers instead of qualitative claims
- **analysis/YYYY-MM-qqq-qqqe.md**: Cash-Flow Anchor section
- Consumed by analyze-macro skill via the context loading step
