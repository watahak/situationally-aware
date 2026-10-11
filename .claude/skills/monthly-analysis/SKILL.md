---
name: monthly-analysis
description: "Full monthly analysis — parallel chart deep dives, macro synthesis, opinion brief, humanizer. Uses subagents for parallelism."
---

# Monthly Analysis — Full Pipeline

One skill, one invocation. Runs preflight, spawns 7 parallel chart agents, then macro synthesis, opinion, and humanizer — all via subagents.

## Steps

### 1. Determine dates

Derive from today's date:
- **YYYY-MM** — e.g. `2026-10`
- **Generated date** — e.g. `2026-10-11`

Use these throughout all steps and agent prompts below.

### 2. Preflight — validate contexts and extract data

Run these two commands in sequence using the Bash tool:

```
.venv/bin/python scripts/validate_contexts.py
```

Note any STALE or ERROR contexts in the output. These are warnings, not blockers.

```
.venv/bin/python scripts/extract_data.py --archive
```

This writes market data to `analysis/YYYY-MM-data.json`.

**GATE:** If extraction fails, STOP and report the error. Do not proceed to chart analysis.

If any contexts are stale, note them but continue — downstream agents will flag stale data in their analysis.

### 3. Chart Analysis — 7 parallel subagents

Spawn ALL 7 Agent calls in a SINGLE message so they run concurrently. Each agent uses `subagent_type: "chart-analyst"`.

For each pair below, launch one Agent with this prompt (substituting the pair's values):

```
Analyze the {NAME} ratio pair (category: {CATEGORY}).

DATA SOURCE: analysis/YYYY-MM-data.json
  - ratio_pairs["{NAME}"], zscores["{NAME}"], heatmap, financialization, fundamentals

OUTPUT FILE: analysis/YYYY-MM-{SLUG}.md
GENERATED DATE: {generated date}
YEAR-MONTH: {YYYY-MM}
```

The 7 pairs:

| Name | Slug | Category |
|------|------|----------|
| SPY / RSP | spy-rsp | concentration |
| QQQ / QQQE | qqq-qqqe | concentration |
| VXUS / SPY | vxus-spy | geographic |
| EWS / EEM | ews-eem | geographic |
| KWEB / MCHI | kweb-mchi | geographic |
| KWEB / QQQ | kweb-qqq | geographic |
| GLD / TLT | gld-tlt | safe-haven |

Wait for all 7 agents to complete before proceeding.

### 4. Macro Synthesis — 1 subagent

Spawn a single Agent (no special agent type — use default) with this prompt:

```
You are writing the monthly Macro Capital Flow Report that synthesizes all per-chart deep dives.

OUTPUT FILE: analysis/YYYY-MM-macro.md

## Instructions

1. Read references/analytical-lens.md. Apply the Detailed Lens (Data Analysis Mode) throughout.
   Read the Context Integration Map and Context Type Handling sections — apply them when integrating context data.

2. Read the extracted data JSON from analysis/YYYY-MM-data.json for cross-referencing.

3. Read ALL context files in the contexts/ directory. For each:
   - Parse the envelope and check freshness
   - Skip if data_as_of is null
   - Apply context type handling rules (structural/seasonal/tactical)

4. Read ALL seven per-chart deep dive files:
   - analysis/YYYY-MM-spy-rsp.md
   - analysis/YYYY-MM-qqq-qqqe.md
   - analysis/YYYY-MM-vxus-spy.md
   - analysis/YYYY-MM-ews-eem.md
   - analysis/YYYY-MM-kweb-mchi.md
   - analysis/YYYY-MM-kweb-qqq.md
   - analysis/YYYY-MM-gld-tlt.md

5. Read .claude/skills/analyze-macro/SKILL.md. Find the "Macro Synthesis Framework" section (starts after "## Macro Synthesis Framework"). Follow that template exactly — it specifies every section the macro report must contain. Also follow the "Writing Rules" section.

6. Cross-reference the per-chart findings. The macro synthesis is where you identify:
   - Which pairs confirm the same capital flow direction (convergence)
   - Which pair tells a different story (outlier)
   - Contradictions between pairs
   - Reinforcing loops where structural risks amplify each other

7. Write the complete report to analysis/YYYY-MM-macro.md.
   Use the generated date. Derive the month/year display from YYYY-MM.

IMPORTANT: The Structural Persistence & Correction Mechanics section must include ALL 5 depression-side and ALL 5 bubble-side mechanisms with current status from this month's data. The Valuation Territory Map must have a row for each of the 7 pairs. The Data Appendix must have all 7 pairs.
```

Replace YYYY-MM placeholders with the actual year-month value.

### 5. Opinion — 1 subagent

Spawn a single Agent with this prompt:

```
You are writing the No-BS Executive Brief from the macro analysis.

OUTPUT FILE: analysis/YYYY-MM-opinion.md

## Instructions

1. Read references/analytical-lens.md. Apply the Condensed Lens (Opinion Mode) throughout.

2. Read the macro report: analysis/YYYY-MM-macro.md
   If it does not exist or is empty, return an error message explaining that the macro synthesis must run first.

3. Read .claude/skills/generate-opinion/SKILL.md. Follow the "Output Template" and "Writing Rules" sections exactly.

4. Generate the opinion brief. Place 2-4 chart embed directives where they directly support the narrative. Valid directives (from the SKILL.md):
   - <!-- chart:ratio:SLUG --> (slugs: spy-rsp, qqq-qqqe, vxus-spy, ews-eem, kweb-mchi, kweb-qqq, gld-tlt)
   - <!-- chart:zscore:SLUG -->
   - <!-- chart:heatmap -->
   - <!-- chart:financialization -->
   - <!-- chart:gauges -->
   - <!-- chart:sankey -->
   - <!-- chart:butterfly -->

5. Write the opinion to analysis/YYYY-MM-opinion.md.
   Use the generated date. Derive month/year from YYYY-MM.

CRITICAL: No dollar signs anywhere in the output — Streamlit renders $ as LaTeX. Write amounts as plain numbers with units (250B/yr, 75B, 4.5%).
Every claim must be tethered to a specific finding from the macro report. No independent analysis.
```

### 6. Humanizer — 1 subagent

Spawn a single Agent with this prompt:

```
Run the humanizer skill in file mode on analysis/YYYY-MM-opinion.md.

1. Read .claude/skills/humanizer/SKILL.md — follow it completely.
2. Read analysis/YYYY-MM-opinion.md — this is the text to edit.
3. Apply every pattern in the skill. Write the edited version back to the same file.

PRESERVE unchanged: chart directives (<!-- chart:... -->), bold signal numbers and ticker pairs, section structure, all factual claims. No dollar signs (Streamlit renders them as LaTeX).
```

### 7. Report

After all steps complete, list:
- All output files created (with paths)
- Any stale contexts that were flagged
- Any chart agents that failed
- Total agent count used
