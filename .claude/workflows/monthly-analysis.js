export const meta = {
  name: 'monthly-analysis',
  description: 'Full monthly macro analysis pipeline: validate, extract, 7 parallel chart deep dives, macro synthesis, opinion brief',
  whenToUse: 'Run monthly to generate the full analysis suite. Replaces the manual /analyze-macro + /generate-opinion sequence.',
  phases: [
    { title: 'Pre-flight', detail: 'Validate contexts and extract market data' },
    { title: 'Chart Analysis', detail: '7 parallel per-pair deep dives', model: 'sonnet' },
    { title: 'Macro Synthesis', detail: 'Cross-referencing synthesis of all charts' },
    { title: 'Opinion Brief', detail: 'Executive brief from macro synthesis' },
    { title: 'Humanize', detail: 'Dedicated humanizer editing pass on opinion' },
  ],
}

// Pair definitions — must stay in sync with settings/market.py ratio_pairs.
// Context mapping is NOT here — agents read references/analytical-lens.md at runtime.
const PAIRS = [
  { name: 'SPY / RSP', slug: 'spy-rsp', category: 'concentration' },
  { name: 'QQQ / QQQE', slug: 'qqq-qqqe', category: 'concentration' },
  { name: 'VXUS / SPY', slug: 'vxus-spy', category: 'geographic' },
  { name: 'EWS / EEM', slug: 'ews-eem', category: 'geographic' },
  { name: 'KWEB / MCHI', slug: 'kweb-mchi', category: 'geographic' },
  { name: 'KWEB / QQQ', slug: 'kweb-qqq', category: 'geographic' },
  { name: 'GLD / TLT', slug: 'gld-tlt', category: 'safe-haven' },
]

const PREFLIGHT_SCHEMA = {
  type: 'object',
  properties: {
    validation_output: { type: 'string' },
    has_stale: { type: 'boolean' },
    stale_contexts: { type: 'array', items: { type: 'string' } },
    extraction_ok: { type: 'boolean' },
    error: { type: 'string' }
  },
  required: ['validation_output', 'has_stale', 'extraction_ok']
}

// Chart prompts are slim — the chart-analyst agent definition (.claude/agents/chart-analyst.md)
// carries the analytical setup, framework loading, context handling, and category guidance.
// The workflow prompt only provides pair-specific parameters.
function buildChartPrompt(pair, ym, genDate) {
  return `Analyze the ${pair.name} ratio pair (category: ${pair.category}).

DATA SOURCE: analysis/${ym}-data.json
  - ratio_pairs["${pair.name}"], zscores["${pair.name}"], heatmap, financialization, fundamentals

OUTPUT FILE: analysis/${ym}-${pair.slug}.md
GENERATED DATE: ${genDate}
YEAR-MONTH: ${ym}`
}

function buildMacroPrompt(ym, genDate) {
  const chartFiles = PAIRS.map(p => `analysis/${ym}-${p.slug}.md`).join('\n   - ')
  return `You are writing the monthly Macro Capital Flow Report that synthesizes all per-chart deep dives.

OUTPUT FILE: analysis/${ym}-macro.md

## Instructions

1. Read references/analytical-lens.md. Apply the Detailed Lens (Data Analysis Mode) throughout.
   Read the Context Integration Map and Context Type Handling sections — apply them when integrating context data.

2. Read the extracted data JSON from analysis/${ym}-data.json for cross-referencing.

3. Read ALL context files in the contexts/ directory. For each:
   - Parse the envelope and check freshness
   - Skip if data_as_of is null
   - Apply context type handling rules (structural/seasonal/tactical)

4. Read ALL seven per-chart deep dive files:
   - ${chartFiles}

5. Read .claude/skills/analyze-macro/SKILL.md. Find the "Macro Synthesis Framework" section (starts after "## Macro Synthesis Framework"). Follow that template exactly — it specifies every section the macro report must contain. Also follow the "Writing Rules" section.

6. Cross-reference the per-chart findings. The macro synthesis is where you identify:
   - Which pairs confirm the same capital flow direction (convergence)
   - Which pair tells a different story (outlier)
   - Contradictions between pairs
   - Reinforcing loops where structural risks amplify each other

7. Write the complete report to analysis/${ym}-macro.md.
   Use "${genDate}" as the generated date. Derive the month/year display from "${ym}".

IMPORTANT: The Structural Persistence & Correction Mechanics section must include ALL 5 depression-side and ALL 5 bubble-side mechanisms with current status from this month's data. The Valuation Territory Map must have a row for each of the 7 pairs. The Data Appendix must have all 7 pairs.`
}

function buildOpinionPrompt(ym, genDate) {
  return `You are writing the No-BS Executive Brief from the macro analysis.

OUTPUT FILE: analysis/${ym}-opinion.md

## Instructions

1. Read references/analytical-lens.md. Apply the Condensed Lens (Opinion Mode) throughout.

2. Read the macro report: analysis/${ym}-macro.md
   If it does not exist or is empty, return an error message explaining that /analyze-macro must run first.

3. Read .claude/skills/generate-opinion/SKILL.md. Follow the "Output Template" and "Writing Rules" sections exactly.

4. Generate the opinion brief. Place 2-4 chart embed directives where they directly support the narrative. Valid directives (from the SKILL.md):
   - <!-- chart:ratio:SLUG --> (slugs: spy-rsp, qqq-qqqe, vxus-spy, ews-eem, kweb-mchi, kweb-qqq, gld-tlt)
   - <!-- chart:zscore:SLUG -->
   - <!-- chart:heatmap -->
   - <!-- chart:financialization -->
   - <!-- chart:gauges -->
   - <!-- chart:sankey -->
   - <!-- chart:butterfly -->

5. Write the opinion to analysis/${ym}-opinion.md.
   Use "${genDate}" as the generated date. Derive month/year from "${ym}".

CRITICAL: No dollar signs anywhere in the output — Streamlit renders $ as LaTeX. Write amounts as plain numbers with units (250B/yr, 75B, 4.5%).
Every claim must be tethered to a specific finding from the macro report. No independent analysis.`
}

function buildHumanizerPrompt(ym) {
  return `Run the humanizer skill in file mode on analysis/${ym}-opinion.md.

1. Read .claude/skills/humanizer/SKILL.md — follow it completely.
2. Read analysis/${ym}-opinion.md — this is the text to edit.
3. Apply every pattern in the skill. Write the edited version back to the same file.

PRESERVE unchanged: chart directives (<!-- chart:... -->), bold signal numbers and ticker pairs, section structure, all factual claims. No dollar signs (Streamlit renders them as LaTeX).`
}

// ═══════════════════════════════════════════════════════════════
// Phase 1: Pre-flight — validate contexts + extract market data
// ═══════════════════════════════════════════════════════════════
phase('Pre-flight')
log('Running context validation and data extraction...')

const preflight = await agent(`Run these two commands in sequence and report structured results.

1. Run: .venv/bin/python scripts/validate_contexts.py
   Capture the full stdout output. Note any STALE or ERROR statuses.
   List the names of any stale contexts.

2. Run: .venv/bin/python scripts/extract_data.py --archive
   This fetches market data via yfinance and writes JSON to analysis/${args.yearMonth}-data.json.

If any context is STALE, include a warning but do NOT abort.
If extraction fails, set extraction_ok to false and include the error message.`, {
  label: 'validate + extract',
  schema: PREFLIGHT_SCHEMA,
  effort: 'low'
})

if (!preflight || !preflight.extraction_ok) {
  log('ABORT: Data extraction failed. ' + (preflight ? preflight.error || 'Unknown error' : 'Agent returned null'))
  return { status: 'failed', phase: 'preflight', error: preflight ? preflight.error : 'agent_null' }
}

if (preflight.has_stale) {
  log('WARNING: Stale contexts: ' + (preflight.stale_contexts || []).join(', ') + ' — analysis will flag these')
}

log('Pre-flight complete. Market data extracted successfully.')

// ═══════════════════════════════════════════════════════════════
// Phase 2: Chart Analysis — 7 parallel per-pair deep dives
// ═══════════════════════════════════════════════════════════════
phase('Chart Analysis')
log('Launching 7 parallel chart analysis agents...')

const chartResults = await parallel(PAIRS.map(pair => () =>
  agent(buildChartPrompt(pair, args.yearMonth, args.generatedDate), {
    label: pair.slug,
    phase: 'Chart Analysis',
    agentType: 'chart-analyst',
    effort: 'medium'
  })
))

const successCount = chartResults.filter(Boolean).length
log('Chart analysis complete: ' + successCount + '/' + PAIRS.length + ' succeeded')

if (successCount < PAIRS.length) {
  const failed = PAIRS.filter(function(_, i) { return !chartResults[i] }).map(function(p) { return p.name })
  log('WARNING: Failed charts: ' + failed.join(', '))
}

// ═══════════════════════════════════════════════════════════════
// Phase 3: Macro Synthesis — cross-reference all charts
// ═══════════════════════════════════════════════════════════════
phase('Macro Synthesis')
log('Generating macro synthesis from ' + successCount + ' chart analyses...')

const macroResult = await agent(buildMacroPrompt(args.yearMonth, args.generatedDate), {
  label: 'macro-synthesis',
  model: 'sonnet',
  effort: 'high'
})

if (!macroResult) {
  log('WARNING: Macro synthesis agent returned null')
}

log('Macro synthesis complete.')

// ═══════════════════════════════════════════════════════════════
// Phase 4: Opinion Brief — executive summary
// ═══════════════════════════════════════════════════════════════
phase('Opinion Brief')
log('Generating opinion brief...')

const opinionResult = await agent(buildOpinionPrompt(args.yearMonth, args.generatedDate), {
  label: 'opinion',
  effort: 'medium'
})

if (!opinionResult) {
  log('WARNING: Opinion agent returned null')
}

log('Opinion brief complete.')

// ═══════════════════════════════════════════════════════════════
// Phase 5: Humanize — dedicated editing pass on opinion
// ═══════════════════════════════════════════════════════════════
phase('Humanize')
log('Running humanizer pass on opinion brief...')

const humanizeResult = await agent(buildHumanizerPrompt(args.yearMonth), {
  label: 'humanize',
  effort: 'high'
})

if (!humanizeResult) {
  log('WARNING: Humanizer agent returned null')
}

log('Humanizer pass complete.')

// ═══════════════════════════════════════════════════════════════
// Return summary
// ═══════════════════════════════════════════════════════════════
return {
  status: 'complete',
  yearMonth: args.yearMonth,
  files: {
    data: 'analysis/' + args.yearMonth + '-data.json',
    charts: PAIRS.map(function(p) { return 'analysis/' + args.yearMonth + '-' + p.slug + '.md' }),
    macro: 'analysis/' + args.yearMonth + '-macro.md',
    opinion: 'analysis/' + args.yearMonth + '-opinion.md'
  },
  preflight: {
    stale_contexts: preflight.stale_contexts || [],
    has_stale: preflight.has_stale
  },
  chart_success_count: successCount,
  total_agents: 11
}
