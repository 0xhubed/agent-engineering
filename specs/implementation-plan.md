# AI Agents Learning Hub - Implementation Plan

## Phase 1: Project Setup & Infrastructure ✅ COMPLETE

### 1.1 Repository Structure
- [x] Initialize project with chosen static site generator (e.g., Astro, Hugo, or plain HTML/CSS)
  - **Choice: Astro** with TypeScript - modern, fast, excellent markdown support
- [x] Set up directory structure matching spec:
  ```
  agent-patterns/
  ├── src/
  │   ├── components/       # CodeBlock, Callout, Table, Diagram
  │   ├── layouts/          # BaseLayout.astro
  │   ├── pages/            # index, topics/, benchmarks/, resources/
  │   ├── styles/           # global.css (Tailwind)
  │   └── content/          # Placeholder for future markdown
  ├── public/               # favicon.svg
  ├── astro.config.mjs
  ├── tailwind.config.mjs
  └── package.json
  ```
- [x] Configure build pipeline and deployment (GitHub Pages, Vercel, or Netlify)
  - **Choice: GitHub Pages** - `.github/workflows/deploy.yml` configured
- [x] Set up CSS framework or design system
  - **Choice: Tailwind CSS** with custom design tokens

### 1.2 Design System
- [x] Define typography, colors, spacing
  - **Typography:** Inter (sans), JetBrains Mono (code) via Google Fonts CDN
  - **Colors:** Primary blue (#3B82F6), Slate grays, accent colors for callouts
- [x] Create reusable components (code blocks, tables, callouts, diagrams)
  - `CodeBlock.astro` - Multi-tab code examples with copy button
  - `Callout.astro` - Info/warning/tip/danger boxes
  - `Table.astro` - Styled responsive tables
  - `Diagram.astro` - ASCII/text diagram container
- [x] Ensure syntax highlighting for Pseudo-code, Python, and C#
  - **Shiki** (Astro built-in) with github-light/github-dark themes
- [x] Mobile-responsive layout
  - Sticky header, collapsible mobile nav, responsive grid

### 1.3 Verification (All Passed)
- [x] `npm install` - Completes without errors
- [x] `npm run dev` - Dev server runs on localhost:4321
- [x] `npm run build` - Generates static site in `dist/` (0 errors, 0 warnings)

---

## Phase 2: Core Content - Foundational Topics ✅ COMPLETE

### 2.1 Tool Use & Function Calling ✅
- [x] Write concept explanation (`topics/tool-use/index.astro`)
- [x] Create code examples in 3 formats (Pseudo-code, Python, C#)
- [x] Document evaluation approach (metrics table, benchmarks)

### 2.2 ReAct Pattern ✅
- [x] Write concept explanation
- [x] Create code examples (pseudo-code, LangGraph, MS Agent Framework)
- [x] Document evaluation criteria (task completion, step efficiency, etc.)

### 2.3 Agent Memory Systems ✅
- [x] Write concept explanation (working, short-term, long-term, episodic)
- [x] Create code examples (custom implementation, Mem0 integration)
- [x] Document evaluation approach (recall accuracy, retention tests)

---

## Phase 3: Context Layer Topics

### 3.1 Context Engineering
- [ ] Write concept explanation (Write, Select, Compress, Isolate strategies)
- [ ] Create code examples
- [ ] Document evaluation approach

### 3.2 Context Bloat & Context Rot
- [ ] Write concept explanation with research findings
- [ ] Create mitigation code examples
- [ ] Document evaluation (needle-in-haystack tests)

### 3.3 Prompt Caching / KV Cache
- [ ] Write concept explanation
- [ ] Create usage examples
- [ ] Document cost/latency impact metrics

---

## Phase 4: Skills Pattern (Anthropic's Approach)

### 4.1 Filesystem as Tool Storage
- [ ] Write concept explanation
- [ ] Create example skill directory structure
- [ ] Document SKILL.md format with examples

### 4.2 Progressive Disclosure
- [ ] Write concept explanation (metadata → instructions → resources)
- [ ] Create implementation examples
- [ ] Document token savings measurements

### 4.3 Database-Backed Tool Discovery
- [ ] Write concept explanation
- [ ] Create examples (Vector DB, Relational, Hybrid)
- [ ] Document evaluation approach

---

## Phase 5: Protocols & Interoperability

### 5.1 MCP (Model Context Protocol)
- [ ] Write concept explanation
- [ ] Create integration examples
- [ ] Document security considerations

### 5.2 A2A (Agent2Agent Protocol)
- [ ] Write concept explanation
- [ ] Create Agent Card examples
- [ ] Document use cases

---

## Phase 6: Learning & Adaptation

### 6.1 Learning in Token Space
- [ ] Write concept explanation
- [ ] Create examples (trajectory storage, dynamic few-shot)
- [ ] Document evaluation approach

### 6.2 Reflexion
- [ ] Write concept explanation
- [ ] Create implementation examples
- [ ] Document pitfalls and mitigations

### 6.3 Self-Evolving Agents
- [ ] Write overview of emerging research (SCA, Gödel Agent, SICA)
- [ ] Create conceptual examples
- [ ] Document evaluation challenges

---

## Phase 7: Multi-Agent Orchestration

### 7.1 Orchestration Patterns
- [ ] Write concept explanation (hierarchical, peer-to-peer, role-based, MoE)
- [ ] Create code examples for each pattern
- [ ] Document evaluation metrics

### 7.2 Framework Comparison
- [ ] Write comparison of LangGraph, CrewAI, AutoGen, MS Agent Framework
- [ ] Create equivalent examples in multiple frameworks
- [ ] Document trade-offs

---

## Phase 8: Agentic RAG

### 8.1 RAG Evolution
- [ ] Write concept explanation (Basic → Agentic → Self-RAG → Corrective)
- [ ] Create implementation examples
- [ ] Document evaluation approach

### 8.2 Graph RAG
- [ ] Write concept explanation
- [ ] Create examples with entity-relationship graphs
- [ ] Document when to use vs traditional RAG

---

## Phase 9: Evaluation & Benchmarks

### 9.1 Evaluation Content
- [ ] Write evaluation taxonomy (`topics/evaluation/index.md`)
- [ ] Document agent-specific metrics (DeepEval)
- [ ] Create benchmark overview (SWE-bench, WebArena, τ-bench)

### 9.2 Benchmarks Infrastructure
- [ ] Create `benchmarks/methodology.md` documenting DGX Spark setup
- [ ] Define JSON schema for results
- [ ] Build `benchmarks/dashboard.html` for results visualization

---

## Phase 10: DGX Spark Experiments (Parallel Track)

These experiments run offline on your DGX Spark. They serve two purposes: your own learning and unique content for the site. Run incrementally as you write related topic content.

### 10.1 Tool Calling Accuracy (Start Here)
**Related topic:** Tool Use & Function Calling

**Setup:**
- [ ] Create dataset of 50-100 function calling tasks with ground truth
- [ ] Include varied complexity: single tool, multi-tool, nested arguments
- [ ] Define schemas in OpenAI and Anthropic formats

**Execution:**
- [ ] Run all models: gpt-oss:20b, gpt-oss:120b, Nemotron-3-Nano, GLM-4.7-Flash, Qwen3-Coder-30B-A3B, DeepSeek-V3.2, MiMo-V2-Flash
- [ ] Measure: exact tool match, argument accuracy, latency, tokens/sec

**Learning goals:**
- How do models parse different schema formats?
- Where do smaller models fail vs larger ones?
- Does tool description quality affect accuracy?

---

### 10.2 Context Degradation Curves
**Related topic:** Context Bloat & Context Rot

**Setup:**
- [ ] Prepare needle-in-haystack test set
- [ ] Create filler content at: 4K, 8K, 16K, 32K, 64K, 128K, 256K, 512K tokens
- [ ] Place "needle" (key fact) at beginning, middle, end positions

**Execution:**
- [ ] Run on Nemotron-3 Nano (claims 1M context) - push to limits
- [ ] Run on other models up to their stated context limits
- [ ] Measure: recall accuracy at each size/position combination

**Learning goals:**
- Where does the "lost in the middle" effect actually appear?
- Does Nemotron's 1M context claim hold up?
- What's the practical vs advertised context limit?

---

### 10.3 Skills Discovery Precision
**Related topic:** Skills Pattern

**Setup:**
- [ ] Create 20+ mock skill folders with realistic SKILL.md files
- [ ] Design 50+ user queries ranging from obvious to ambiguous
- [ ] Define ground truth: which skill(s) should be selected

**Execution:**
- [ ] Test models' ability to select correct skill from filesystem listing
- [ ] Test with metadata only vs full SKILL.md content
- [ ] Measure: Precision@1, Precision@3, false positive rate

**Learning goals:**
- How much metadata is enough for accurate routing?
- Do models get confused by similar skill descriptions?
- Token cost of metadata-only vs full SKILL.md?

---

### 10.4 Reasoning Model Comparison
**Related topic:** ReAct Pattern

**Setup:**
- [ ] Create 30+ multi-step reasoning tasks (math, logic, planning)
- [ ] Prepare prompts with and without explicit Chain-of-Thought instructions

**Execution:**
- [ ] Compare DeepSeek-V3.2 vs gpt-oss:120b vs Qwen3-Coder-30B-A3B
- [ ] Run each task: baseline, with CoT prompt, with ReAct prompt
- [ ] Measure: accuracy, step count, latency

**Learning goals:**
- Do reasoning-trained models (DeepSeek-R1) benefit from explicit CoT?
- Is the "diminishing returns of CoT on reasoning models" claim true?
- Cost/quality tradeoff between model sizes?

---

### 10.5 Multi-Model Orchestration (Unique to DGX Spark)
**Related topic:** Multi-Agent Orchestration

**Setup:**
- [ ] Design 20+ tasks requiring planning + execution + evaluation
- [ ] Configure supervisor-worker architecture:
  - Supervisor: Nemotron-3-Nano (planning, 1M context)
  - Worker: gpt-oss:20b or GLM-4.7-Flash (execution)
  - Evaluator: Qwen3-Coder-30B-A3B (quality check)

**Execution:**
- [ ] Run tasks with multi-model setup
- [ ] Run same tasks with single large model (gpt-oss:120b or DeepSeek-V3.2)
- [ ] Measure: task completion, total latency, coordination overhead, quality

**Learning goals:**
- When does multi-model beat single-model?
- What's the coordination overhead cost?
- Which model combinations work best for which tasks?

---

### 10.6 Memory Retention Over Turns
**Related topic:** Agent Memory Systems

**Setup:**
- [ ] Design 20+ multi-turn conversations (10-50 turns each)
- [ ] Insert key facts at various points that must be recalled later
- [ ] Include distractors and topic changes

**Execution:**
- [ ] Test raw context window (no memory system)
- [ ] Test with summarization at thresholds
- [ ] Measure: fact recall accuracy at turn N, token usage

**Learning goals:**
- At what turn count does recall degrade?
- How much does summarization help vs hurt?
- Optimal summarization threshold?

---

### 10.7 General-Purpose Agent Evaluation
**Related topic:** All foundational topics (Tool Use, ReAct, Memory)

**Setup:**
- [ ] Design 50-100 tasks across 5 categories:
  - **File operations:** Read config, parse JSON/YAML, create/modify/delete files
  - **Calculations:** Parse data, compute statistics, unit conversions, date math
  - **Coding:** Write functions, fix bugs, refactor code, add tests
  - **Information synthesis:** Read multiple files, summarize, cross-reference
  - **Multi-step workflows:** Chained operations (e.g., "bump version in package.json and update changelog")
- [ ] Define 3 difficulty levels:
  - Easy: 2-3 tool calls, linear flow
  - Medium: 3-5 tool calls, some branching
  - Hard: 5+ tool calls, error handling required
- [ ] Create ground truth for each task (expected output or file state)
- [ ] Set up sandboxed filesystem environment for safe execution

**Execution:**
- [ ] Run all models on full task set
- [ ] Measure per-category and per-difficulty:
  - Task completion rate (binary: pass/fail)
  - Step efficiency (actual steps vs optimal)
  - Error recovery (did model retry on failure?)
  - Time to completion
- [ ] Analyze failure modes by category

**Learning goals:**
- Which models handle multi-tool orchestration best?
- Where do models fail — planning, execution, or recovery?
- Does performance vary by task category (e.g., strong at coding, weak at file ops)?
- Cost vs quality tradeoff across model sizes

**Example tasks:**
```
Easy: "Read config.json and return the value of 'api_version'"
Medium: "Find all TODO comments in src/*.py and write them to TODO.md"
Hard: "The tests in test_auth.py are failing. Debug, fix the issue, and verify tests pass"
```

---

### 10.8 Trading Backtesting Benchmark
**Related topic:** Multi-Agent Orchestration, Learning & Adaptation

**Leverages:** [Agent Arena](../agent-arena/) — existing crypto futures trading competition platform

**Objective:** Compare pure reasoning vs agentic setups on real trading decisions with measurable financial outcomes.

**Setup:**
- [ ] Prepare historical market data periods covering different regimes:
  - Bull market (trending up)
  - Bear market (trending down)
  - Choppy/sideways (range-bound)
- [ ] Configure standardized test conditions:
  - Starting capital: $10,000 per agent
  - Symbols: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, DOGEUSDT
  - Tick interval: 5 minutes
  - Max leverage: 10x
  - Fees: 0.04% taker, 0.02% maker
- [ ] Define 4 agent configurations per model:

| Configuration | Description | Tools | Skills |
|---------------|-------------|-------|--------|
| Pure Reasoning | Decide from market data alone | None | None |
| Agentic (Tools) | Can call indicators, check positions | RSI, SMA, MACD, Bollinger | None |
| Skill-Aware | Reads learned SKILL.md before deciding | None | Yes |
| Full Agentic | Tools + Skills combined | All | Yes |

- [ ] Prepare baseline agents for comparison:
  - TA Bot (RSI + SMA rules-based)
  - Index Fund (buy-and-hold 20% per symbol)
  - Random Agent

**Execution:**

Full test matrix — every model × configuration × regime:

```
Models (5):
├── gpt-oss:20b
├── gpt-oss:120b
├── Nemotron-3-Nano
├── GLM-4.7-Flash
└── Qwen3-Coder-30B-A3B

× Configurations (4):
├── Pure Reasoning (no tools, no skills)
├── Agentic Tools (RSI, SMA, MACD, Bollinger)
├── Skill-Aware (SKILL.md files only)
└── Full Agentic (tools + skills)

× Market Regimes (3):
├── Bull (trending up)
├── Bear (trending down)
└── Choppy (sideways/range-bound)

= 60 model runs

+ Baselines (3) × Regimes (3):
├── TA Bot (rules-based)
├── Index Fund (buy-and-hold)
└── Random Agent

= 9 baseline runs

TOTAL: 69 runs
```

- [ ] Run full matrix (69 runs)
- [ ] Record all decisions with reasoning for analysis
- [ ] Collect metrics per run:
  - **Returns:** Total PnL, PnL %, daily returns
  - **Risk:** Max drawdown, Sharpe ratio, Sortino ratio
  - **Behavior:** Trade count, win rate, avg hold time, liquidations
  - **Efficiency:** Tokens used, latency per decision

**Analysis:**

Comparison dimensions:

| Dimension | Example Questions |
|-----------|-------------------|
| Model vs Model | "Which model has highest Sharpe in Pure Reasoning?" |
| Config vs Config | "Does gpt-oss:120b benefit more from tools than GLM-4.7-Flash?" |
| Regime vs Regime | "Which config handles bear markets best across all models?" |
| Cost-adjusted | "Best PnL per dollar of inference cost?" |
| Skill transfer | "Is Skill-Aware ever better than Full Agentic?" |

- [ ] Build comparison tables:
  - Models ranked by PnL (per config, per regime)
  - Configurations ranked by Sharpe (per model)
  - Risk-adjusted leaderboard (Sortino across all runs)
- [ ] Identify patterns:
  - Does tool access always help, or only for some models?
  - Do larger models benefit more from skills?
  - Which regime is hardest for all models?
- [ ] Examine failure modes:
  - Liquidation analysis (what decisions led to blowups?)
  - Overtrading detection (trade count vs performance)
- [ ] Calculate cost-adjusted returns (PnL per $ of inference cost)

**Learning goals:**
- Does tool access improve trading performance?
- Do learned skills transfer effectively?
- Which models handle financial reasoning best?
- Is there a configuration that dominates across regimes?
- What's the optimal balance of reasoning vs tool use for trading?

**Unique value:**
- Real financial metrics (not proxy scores)
- Tests knowledge transfer (skills pattern in action)
- Domain-specific benchmark (finance/trading)
- Comparable to human trader benchmarks

---

### Experiment Execution Order

Recommended sequence based on learning progression:

| Order | Experiment | Why This Order |
|-------|------------|----------------|
| 1 | Tool Calling Accuracy | Baseline, simple to set up, foundational |
| 2 | General-Purpose Agent | Holistic view after baseline, reveals strengths/weaknesses |
| 3 | Context Degradation | Tests core model capabilities |
| 4 | Skills Discovery | Tests the key differentiating pattern |
| 5 | Reasoning Comparison | Builds on tool calling baseline |
| 6 | Memory Retention | More complex setup |
| 7 | Trading Backtesting | Domain-specific, leverages existing infra, real metrics |
| 8 | Multi-Model Orchestration | Most complex, requires learnings from above |

---

## Phase 11: Guardrails & Safety

### 11.1 OWASP Top 10 for LLM Applications
- [ ] Write overview of key risks
- [ ] Create mitigation examples
- [ ] Document testing approaches

### 11.2 Guardian Agents
- [ ] Write pattern explanation
- [ ] Create implementation examples
- [ ] Document evaluation criteria

---

## Phase 12: Resources & Polish

### 12.1 Resources Section
- [ ] Compile `resources/papers.md` with research references
- [ ] Write `resources/frameworks.md` with framework comparison

### 12.2 Navigation & UX
- [ ] Build main index page with topic navigation
- [ ] Add search functionality (optional)
- [ ] Add "last updated" timestamps
- [ ] Cross-link related topics

### 12.3 Final Review
- [ ] Technical review of all code examples
- [ ] Proofread all content
- [ ] Test all links
- [ ] Validate on multiple browsers/devices

---

## Milestone Summary

| Phase | Description | Dependencies | Status |
|-------|-------------|--------------|--------|
| 1 | Project Setup | None | ✅ Complete |
| 2 | Foundational Topics | Phase 1 | ✅ Complete |
| 3 | Context Layer | Phase 1 | Ready to start |
| 4 | Skills Pattern | Phase 1 | Ready to start |
| 5 | Protocols | Phase 1 | Ready to start |
| 6 | Learning & Adaptation | Phase 2 | Ready to start |
| 7 | Multi-Agent | Phase 2 | Ready to start |
| 8 | Agentic RAG | Phase 2 | Ready to start |
| 9 | Evaluation Content & Infrastructure | Phase 1 | Ready to start |
| 10 | DGX Spark Experiments | Phase 1, run alongside 2-8 | Ready to start |
| 11 | Guardrails & Safety | Phase 1 | Ready to start |
| 12 | Resources & Polish | Phases 2-11 | Blocked |

---

## Notes

- Phases 2-8, 10, and 11 can be worked on in parallel after Phase 1 is complete
- **Phase 10 (Experiments) is a parallel learning track** — run experiments as you write related topic content
- Start with Experiment 10.1 (Tool Calling) as your baseline before others
- Consider launching with 3-4 topics + their benchmark results, then expand
- Each experiment result becomes unique content that differentiates your site

---

## Progress Log

### 2026-01-26: Phase 2 Complete
- Created Tool Use & Function Calling topic page
  - Basic tool execution patterns
  - Parallel tool execution
  - Error handling and retries
  - Trade-offs table (static vs dynamic vs skills pattern)
  - Evaluation metrics and frameworks
- Created ReAct Pattern topic page
  - Basic ReAct loop implementation
  - Explicit reasoning traces with parsing
  - Modern implicit reasoning approach
  - Evolution from 2022 to 2025 (explicit → implicit)
  - Trajectory analysis and debugging
- Created Agent Memory Systems topic page
  - Four memory types: working, short-term, long-term, episodic
  - Summarization strategies for context compression
  - Episodic memory for learning from experience
  - Mem0 integration example
  - Evaluation approach (recall accuracy, retention tests)
- Updated Topics index with categories and available status
- Updated Home page with available/coming soon indicators
- All topics include code in 3 formats: Pseudo-code, Python, C#

### 2025-01-26: Phase 1 Complete
- Initialized Astro project with TypeScript
- Configured Tailwind CSS with custom design tokens
- Created base layout with header, footer, mobile nav, dark mode toggle
- Built reusable components: CodeBlock (tabbed), Callout, Table, Diagram
- Created placeholder pages: Home, Topics, Benchmarks, Resources
- Set up GitHub Pages deployment workflow
- All verification checks passed
