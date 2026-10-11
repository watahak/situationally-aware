# Monthly Analysis Workflow

Orchestrates the full macro analysis pipeline with parallel chart analysis, replacing the manual `/analyze-macro` + `/generate-opinion` sequence.

## Architecture

```
Phase 1: Pre-flight (1 agent, effort: low)
    validate_contexts.py → extract_data.py
    Gate: abort if extraction fails; warn on stale contexts
         |
Phase 2: Chart Analysis (7 agents in parallel, model: sonnet)
    Each reads: extracted JSON, analytical lens, mapped contexts
    Each writes: analysis/YYYY-MM-{slug}.md
    ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
    │ SPY/RSP  │ QQQ/QQQE │ VXUS/SPY │ EWS/EEM  │KWEB/MCHI │ KWEB/QQQ │ GLD/TLT  │
    └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘
         └──────────┴──────────┴──────────┼──────────┴──────────┴──────────┘
                                          ↓ barrier (macro needs ALL charts)
Phase 3: Macro Synthesis (1 agent, effort: high)
    Reads all 7 chart MDs + JSON + contexts
    Writes: analysis/YYYY-MM-macro.md
                                          |
Phase 4: Opinion + Humanize (1 agent, model: sonnet)
    Reads macro report, generates opinion, humanizes inline
    Writes: analysis/YYYY-MM-opinion.md
```

Total: 10 agents. Wall-clock is dominated by Phase 2 (7 concurrent chart agents).

### Custom agent type: chart-analyst

The chart analysis agents use a custom agent type defined at `.claude/agents/chart-analyst.md`. This separates *how to analyze* (the agent definition) from *what to analyze* (the workflow prompt):

- **Agent definition** carries: analytical lens loading, framework template loading, context integration map reading, freshness handling rules, category-specific guidance, writing rules
- **Workflow prompt** carries: pair name, slug, category, data file path, output file path, dates

This means:
- The workflow script stays slim (chart prompts are ~6 lines each)
- The agent definition is reusable outside the workflow (e.g. ad-hoc single-pair analysis)
- Updating the analysis approach only requires changing the agent definition, not the workflow

## Usage

The workflow is invoked via the Workflow tool with:

```
name: "monthly-analysis"
args: { "yearMonth": "2026-10", "generatedDate": "2026-10-11" }
```

### Prerequisites

1. **Contexts populated.** Paste prompts from `prompts/*.md` into a web-connected LLM (e.g. Gemini), save structured results to `contexts/*.json`. The workflow warns on stale contexts but does not abort.

2. **Python venv available.** `.venv/bin/python` must resolve. Run `source .venv/bin/activate` if needed.

3. **args required.** `Date.now()` is unavailable in workflow scripts, so `yearMonth` and `generatedDate` must be passed explicitly.

### Output files

| File | Phase | Content |
|------|-------|---------|
| `analysis/YYYY-MM-data.json` | Pre-flight | Archived market data extraction |
| `analysis/YYYY-MM-spy-rsp.md` | Chart Analysis | SPY / RSP deep dive |
| `analysis/YYYY-MM-qqq-qqqe.md` | Chart Analysis | QQQ / QQQE deep dive |
| `analysis/YYYY-MM-vxus-spy.md` | Chart Analysis | VXUS / SPY deep dive |
| `analysis/YYYY-MM-ews-eem.md` | Chart Analysis | EWS / EEM deep dive |
| `analysis/YYYY-MM-kweb-mchi.md` | Chart Analysis | KWEB / MCHI deep dive |
| `analysis/YYYY-MM-kweb-qqq.md` | Chart Analysis | KWEB / QQQ deep dive |
| `analysis/YYYY-MM-gld-tlt.md` | Chart Analysis | GLD / TLT deep dive |
| `analysis/YYYY-MM-macro.md` | Macro Synthesis | Cross-referencing macro report |
| `analysis/YYYY-MM-opinion.md` | Opinion Brief | Executive brief (humanized) |

## Pipeline stages

### Phase 1: Pre-flight

A single low-effort agent runs `scripts/validate_contexts.py` (checks all context JSONs for schema validity and freshness) then `scripts/extract_data.py` (fetches yfinance data, computes metrics, archives to `analysis/`). Returns structured results. The pipeline aborts if extraction fails. Stale contexts trigger a warning but the pipeline continues, and downstream agents flag stale data in their analysis.

### Phase 2: Chart Analysis

Seven agents run concurrently, one per ratio pair, using the `chart-analyst` custom agent type (`.claude/agents/chart-analyst.md`). The agent definition handles all the analytical setup — the workflow only passes pair-specific parameters (name, slug, category, data path, output path).

Each agent:
- Reads `references/analytical-lens.md` for the Detailed Lens and Context Integration Map
- Reads the extracted JSON, focusing on its pair's data
- Reads relevant context files (determined from the integration map at runtime, not hardcoded)
- Reads the Per-Chart Deep Dive Framework from `.claude/skills/analyze-macro/SKILL.md`
- Writes its analysis to `analysis/YYYY-MM-{slug}.md`

Uses `parallel()` (barrier) because Phase 3 needs ALL chart outputs before it can cross-reference.

### Phase 3: Macro Synthesis

A single agent with `effort: high` reads all 7 chart deep dives, the extracted JSON, all contexts, and the Macro Synthesis Framework from the analyze-macro SKILL.md. It cross-references findings across pairs to identify convergence, outliers, contradictions, and reinforcing loops. Writes the macro report.

### Phase 4: Opinion + Humanize

A single agent reads the macro report and the opinion template from `.claude/skills/generate-opinion/SKILL.md`. It generates the executive brief with 2-4 embedded chart directives, then applies a humanizer pass inline (removing AI writing patterns) before writing the final output. This replaces the two-step process of generate-opinion then humanizer.

## Maintenance

### Adding a new ratio pair

1. Add to `CONFIG["ratio_pairs"]` in `settings/market.py`
2. Add to `CONFIG["zscore_pairs"]` if Z-score tracking desired
3. Add tickers to the appropriate category list and `heatmap_tickers`
4. Add a new entry to the `PAIRS` array in `monthly-analysis.js` with name, slug, and category
5. If the new pair should consume specific contexts, update the Context Integration Map in `references/analytical-lens.md`

### Adding a new context file

1. Create the prompt in `prompts/new-context.md`
2. Create the JSON template in `contexts/new-context.json`
3. Update the Context Integration Map in `references/analytical-lens.md` to map the context to its relevant pairs

The workflow adapts automatically — agents read the integration map at runtime.

### Resuming a failed run

If the workflow is interrupted (killed, timed out, error in a late phase), use `resumeFromRunId` with the run ID from the original invocation. Completed agent calls with unchanged prompts return cached results instantly. Only the interrupted or subsequent agents re-run.

## Comparison with serial skills

| | Workflow (`monthly-analysis`) | Serial skills (`/analyze-macro` + `/generate-opinion`) |
|---|---|---|
| **Invocation** | Single workflow call | Two manual skill invocations |
| **Chart analysis** | 7 agents in parallel | 1 agent, all 7 charts serial |
| **Interactive checkpoint** | Pre-flight validation (automated) | FLAG step waits for user confirmation |
| **Opinion + humanizer** | Single agent, inline | Two separate skill invocations |
| **Resume on failure** | `resumeFromRunId` caches completed work | Must re-run from scratch |
| **Wall-clock** | ~5 min | ~15 min |
| **When to use** | Full monthly analysis run | Ad-hoc single-pair re-analysis, or re-generating just the opinion |

The existing skills remain available. Use `/analyze-macro` when you want the interactive checkpoint or need to re-run a single pair's analysis. Use `/generate-opinion` when the macro report is already current and you just want a new opinion brief.

## Agentic concepts reference

This workflow demonstrates several core agentic patterns:

### Fan-out / fan-in

Phase 2 fans out to 7 independent chart agents running concurrently. Phase 3 fans in, reading all their outputs. This is the most common parallelization pattern: split independent work across agents, then synthesize.

**When to use:** Whenever N items can be processed independently and a later stage needs all results. The speedup is proportional to N (minus overhead).

### Barrier vs pipeline

Phase 2 uses `parallel()` (a barrier) rather than `pipeline()`. A barrier waits for ALL agents to complete before continuing. This is correct here because the macro synthesis cross-references ALL chart findings — it genuinely needs the full set.

**When to use barriers:** Only when the next stage needs ALL prior-stage results together (dedup, cross-reference, early-exit on count). If items flow independently through stages, use `pipeline()` instead — it lets fast items proceed without waiting for slow ones.

### Guardrail gate

Phase 1 validates contexts and extracts data before any expensive LLM work. If extraction fails, the pipeline aborts immediately. This prevents wasting 7+ agent calls on bad data.

**When to use:** Before any expensive fan-out. Validate inputs cheaply, fail fast.

### Context isolation

Each chart agent reads only the contexts relevant to its pair (determined from the integration map). The SPY/RSP agent does not load physical-anchors data it will never use. This reduces noise and keeps each agent focused.

**When to use:** When agents could be confused or distracted by irrelevant context. Give each agent exactly what it needs, no more.

### Structured data contracts

The `args` object, the pre-flight schema, and the context JSON envelope are all typed interfaces between components. The pre-flight agent returns `{ extraction_ok, has_stale, stale_contexts }` — not prose. The workflow script makes control-flow decisions on these fields.

**When to use:** Whenever an agent's output drives downstream logic. Schemas force the agent to return parseable, typed data instead of natural language that requires interpretation.

### Human-in-the-loop

The `contexts/*.json` files are manually populated by the user pasting Gemini outputs. The pipeline runs without them (graceful degradation) but produces richer analysis with them. This is a deliberate injection point where human-gathered data enriches automated analysis.

**When to use:** When some data is best gathered by humans (paywalled sources, judgment calls, external systems without APIs). Design the pipeline to work without it and improve with it.

### Idempotent stages

Every output file has a deterministic path (`analysis/YYYY-MM-{slug}.md`). Running the workflow twice for the same month overwrites the same files cleanly. Combined with `resumeFromRunId`, this means interrupted runs can resume without re-doing completed work.

**When to use:** Always. Design stages so same inputs produce same outputs and re-runs are safe.

### Custom agent types (separation of concerns)

The `chart-analyst` agent definition separates *how to analyze* from *what to analyze*. The workflow script is the orchestrator (data flow, parallelism, sequencing). The agent definition is the specialist (analytical framework, domain rules, output format). This means the workflow stays simple even as the analysis approach evolves.

**When to use:** When multiple agents share the same expertise or methodology. Define the expertise once as an agent type, then spawn instances with different parameters.

### Single source of truth

Agents read framework templates from SKILL.md files and context mappings from `references/analytical-lens.md` at runtime. The workflow script does not duplicate these — if the analytical framework changes, all agents pick up the change automatically.

**When to use:** When multiple agents need the same instructions or data. Point them at the canonical source rather than copying content into each prompt.
