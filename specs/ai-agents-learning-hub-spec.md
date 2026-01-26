# AI Agents Learning Hub

> A comprehensive educational resource for building, evaluating, and deploying AI agents — from foundational concepts to cutting-edge techniques.

---

## Vision

The AI Agents Learning Hub is designed for **experienced practitioners** who want to go beyond basic prompting and understand the architectural patterns, protocols, and evaluation techniques that power production-grade AI agents.

**What makes this different:**
- Deep dives with **code examples** in Pseudo-code, Python (LangChain/LangGraph), and C# (Microsoft Agent Framework)
- Focus on **cutting-edge topics**: Skills pattern, context engineering, learning in token space
- **Real benchmark results** from open-source models running on local hardware (NVIDIA DGX Spark)
- **Evaluation-first mindset**: Every topic includes how to measure if it's working

---

## Target Audience

- AI/ML engineers building agent systems
- Software developers transitioning to AI roles
- Technical leads evaluating agent architectures
- Researchers exploring agentic AI patterns

**Prerequisites:** Familiarity with LLMs, basic prompting, Python or C#

---

## Topic Structure

### 1. Foundational Concepts

#### 1.1 Tool Use & Function Calling
The bridge between language models and real-world actions.

**Key Concepts:**
- Function calling schemas (OpenAI, Anthropic, open models)
- Tool registration and discovery
- Parallel vs sequential tool execution
- Error handling and retries

**Trade-offs:**
| Approach | Pros | Cons |
|----------|------|------|
| Static tool list | Simple, predictable | Context bloat with many tools |
| Dynamic discovery | Scales better | Additional latency |
| Tool clustering | Balance of both | Complexity in routing |

---

#### 1.2 ReAct Pattern
Reasoning + Acting: The foundational loop for agentic behavior.

**Key Concepts:**
- Thought → Action → Observation cycle
- When to reason vs when to act
- Trajectory analysis and debugging

**Evolution:**
- Original ReAct (2022): Explicit reasoning traces
- Modern approach: Reasoning models (o1, DeepSeek-R1) internalize this
- Observation: CoT prompting shows diminishing returns (3-5%) on reasoning models

---

#### 1.3 Agent Memory Systems

**Memory Types:**
| Type | Scope | Implementation |
|------|-------|----------------|
| Working Memory | Current conversation | Context window |
| Short-term | Current session | In-memory store |
| Long-term | Cross-session | Vector DB + metadata |
| Episodic | Specific interactions | Indexed experiences |

**Key Insight:** Memory systems like Mem0 achieve 80% token reduction while preserving fidelity through intelligent summarization and retrieval.

---

### 2. Context Layer (Hot Topic in 2025)

#### 2.1 Context Engineering
The discipline of optimizing what goes into the context window.

**The Four Strategies:**
1. **Write**: Scratchpads, working memory within context
2. **Select**: Retrieve only relevant information
3. **Compress**: Summarize, deduplicate, prune
4. **Isolate**: Separate concerns into different contexts

**Why it matters:** Context engineering is replacing "prompt engineering" as the key skill for agent developers.

---

#### 2.2 Context Bloat & Context Rot

**Context Bloat:** Performance degradation even within supported context limits.

**Research Findings:**
- "Lost in the middle" effect: Models attend poorly to middle content
- Smaller, curated context often outperforms maxed-out context
- Performance curves are non-linear with context size

**Context Rot:** Outdated information in context contaminates decisions over long-running agents.

**Mitigation Strategies:**
```
function manage_context(history, max_tokens):
    if token_count(history) > threshold:
        # Compress older messages
        old, recent = split_at_recency(history)
        summarized = llm.summarize(old)
        return summarized + recent
    return history
```

---

#### 2.3 Prompt Caching / KV Cache

**How it works:**
- Store Key and Value matrices from attention computation
- Reuse for messages with matching prefixes
- Dramatic cost and latency reduction

**Impact:**
| Metric | Improvement |
|--------|-------------|
| Cost | 50-90% reduction |
| Latency | 30-80% reduction |
| TTFT | Significant improvement |

**When to use:**
- Long system prompts
- Repeated tool definitions
- Multi-turn conversations with stable prefix

---

### 3. Skills Pattern (Anthropic's Approach)

#### 3.1 Filesystem as Tool Storage

**Core Insight:** Instead of loading all tools into context upfront, let the agent discover tools by exploring the filesystem.

**Token Savings Example:**
- Traditional: 150,000 tokens (all tools loaded)
- Skills pattern: 2,000 tokens (on-demand loading)
- **Savings: 98.7%**

**Structure:**
```
skills/
├── salesforce/
│   ├── SKILL.md           # Metadata + instructions
│   ├── createLead.ts      # Tool implementation
│   ├── updateRecord.ts
│   └── references/
│       └── schema.json
├── google-drive/
│   ├── SKILL.md
│   └── getDocument.ts
```

**SKILL.md Format:**
```yaml
---
name: salesforce-tools
description: Tools for Salesforce CRM operations including 
  lead management, record updates, and reporting.
---

# Salesforce Tools

## When to Use
- User mentions CRM, leads, opportunities, accounts
- Requests involving customer data management

## Available Tools
- `createLead`: Create new sales lead
- `updateRecord`: Modify existing records
- `runReport`: Execute Salesforce reports

## Usage Notes
- Always validate record IDs before updates
- Use bulk operations for >10 records
```

---

#### 3.2 Progressive Disclosure

**Three Levels:**
1. **Metadata** (always loaded): ~100 tokens per skill
   - Name and description only
   - Agent decides relevance

2. **Instructions** (loaded on trigger): ~500-2000 tokens
   - Full SKILL.md content
   - Workflows and guidelines

3. **Resources** (loaded on demand): Unlimited
   - Scripts executed without context loading
   - Reference files read as needed

---

#### 3.3 Database-Backed Tool Discovery

**Extending the pattern:** Use semantic search over a skills database.

**Architecture:**
```
User Query: "I need to update our CRM with the new leads"
    │
    ▼
┌─────────────────────────────────────┐
│         Skills Database             │
│  ┌─────────────┐  ┌──────────────┐ │
│  │ Vector DB   │  │ Metadata DB  │ │
│  │ (Embeddings)│  │ (Structured) │ │
│  └─────────────┘  └──────────────┘ │
└─────────────────────────────────────┘
    │
    ▼
Semantic Search: "CRM", "leads", "update"
    │
    ▼
Returns: salesforce/SKILL.md (score: 0.92)
    │
    ▼
Agent loads skill, executes tools
```

**Implementation Options:**
| Storage | Use Case | Pros | Cons |
|---------|----------|------|------|
| Vector DB (Qdrant, Chroma) | Semantic search | Fuzzy matching | Requires embeddings |
| Relational DB | Structured queries | Fast, precise | Exact match only |
| Hybrid | Production systems | Best of both | Complexity |

---

### 4. Protocols & Interoperability

#### 4.1 MCP (Model Context Protocol)

**What it is:** Anthropic's standardized protocol for model-to-tool connections — "USB-C for AI"

**Key Features:**
- Standardized tool discovery and invocation
- 1000+ community servers available
- Supported by major IDEs (VS Code, Cursor)

**Security Considerations:**
- Tool poisoning: Malicious tool definitions
- Cross-server shadowing: Name collisions
- Data exfiltration via tool responses

---

#### 4.2 A2A (Agent2Agent Protocol)

**What it is:** Google's protocol for multi-agent communication

**Key Features:**
- Agent Cards at `/.well-known/agent.json`
- Task delegation and handoff
- Backed by 50+ companies (Microsoft, Salesforce, IBM)
- Now under Linux Foundation governance

**Use Cases:**
- Enterprise agent ecosystems
- Cross-organization agent collaboration
- Marketplace of specialized agents

---

### 5. Learning & Adaptation

#### 5.1 Learning in Token Space

**Paradigm Shift:** Update tokens/context instead of model weights.

> "Weights are temporary, learned context persists." — Letta/MemGPT concept

**Approaches:**
- Store successful trajectories as in-context examples
- Experience replay for prompting
- Dynamic few-shot selection based on task similarity

---

#### 5.2 Reflexion

**How it works:**
1. Agent attempts task
2. On failure, generates natural language reflection
3. Reflection stored as episodic memory
4. Future attempts informed by past reflections

**No gradient updates required** — pure in-context learning.

**Pitfalls:**
- Confirmation bias in self-reflection
- Mode collapse (same reflection patterns)
- Requires good failure detection

---

#### 5.3 Self-Evolving Agents

**Emerging Research:**
- **SCA (Self-Challenging Agent)**: Generates own test cases
- **Gödel Agent**: Self-referential improvement
- **SICA**: Edits own codebase

**Trajectory Optimization:**
- StarPO framework
- Rollout freshness matters
- AgentDiet: 80% cost savings through trajectory pruning

---

### 6. Multi-Agent Orchestration

#### 6.1 Patterns

| Pattern | Description | Use Case |
|---------|-------------|----------|
| Hierarchical | Supervisor delegates to workers | Complex workflows |
| Peer-to-peer | Agents communicate directly | Collaborative tasks |
| Role-based | Researcher → Writer → Critic | Content generation |
| Mixture of Experts | Route to specialist agents | Diverse task types |

**Research Finding:** Multi-agent systems show 45% faster problem resolution and 60% more accurate results than single-agent approaches.

---

#### 6.2 Frameworks Comparison

| Framework | Architecture | Strengths |
|-----------|--------------|-----------|
| LangGraph | DAG-based | Explicit control flow |
| CrewAI | Role-based | Quick prototyping |
| AutoGen | Event-driven | Flexible communication |
| Microsoft Agent Framework | Unified | Enterprise-ready, .NET support |

---

### 7. Agentic RAG

#### 7.1 Beyond Simple Retrieval

**Evolution:**
- Basic RAG: Single retrieval step
- Agentic RAG: Agent decides when/what to retrieve
- Self-RAG: Model decides if retrieval needed
- Corrective RAG: Validates and improves context

---

#### 7.2 Graph RAG

**When to use:** Questions requiring global/thematic understanding across documents.

**How it works:**
1. Build entity-relationship graph from documents
2. Community detection for topic clusters
3. Query expansion using graph structure
4. Multi-hop reasoning across relationships

---

### 8. Evaluation & Benchmarks

#### 8.1 Evaluation Taxonomy

**What to Evaluate:**

| Category | Metrics |
|----------|---------|
| Behavior | Task completion, output quality, latency, cost |
| Capabilities | Tool use, reasoning, planning |
| Reliability | Consistency, error recovery |
| Safety | Guardrail compliance, harmful output prevention |

**How to Evaluate:**

| Method | Description | Use Case |
|--------|-------------|----------|
| Deterministic | Code runs, tests pass | Coding agents |
| LLM-as-Judge | Model evaluates output | Quality assessment |
| Human evaluation | Expert review | Final validation |
| Rubric-based | Structured criteria | Consistent scoring |

---

#### 8.2 Agent-Specific Metrics

From DeepEval framework:

| Metric | What it Measures |
|--------|------------------|
| TaskCompletionMetric | Did the agent accomplish the goal? |
| PlanQualityMetric | Is the plan logical, complete, efficient? |
| PlanAdherenceMetric | Did the agent follow its plan? |
| StepEfficiencyMetric | Any redundant or unnecessary steps? |
| ToolCorrectnessMetric | Right tools selected? |
| ArgumentCorrectnessMetric | Correct parameters passed? |

---

#### 8.3 Key Benchmarks

| Benchmark | Focus | Current SOTA |
|-----------|-------|--------------|
| SWE-bench Verified | GitHub issue resolution | 65%+ |
| WebArena | Web task automation | ~60% |
| τ-bench (Sierra) | Multi-turn + policy compliance | — |
| Terminal-Bench | End-to-end technical tasks | — |
| Context-Bench (Letta) | Long-context reasoning | — |

---

### 9. Guardrails & Safety

#### 9.1 OWASP Top 10 for LLM Applications

Key risks for agent systems:
- Prompt injection (direct and indirect)
- Insecure tool use
- Excessive agency
- Data leakage through tools

---

#### 9.2 Guardian Agents

**Pattern:** Dedicated agent that monitors and can veto unsafe actions.

```
User Request
    │
    ▼
┌─────────────┐     ┌─────────────┐
│ Main Agent  │────▶│  Guardian   │
│ (executes)  │     │  (monitors) │
└─────────────┘     └─────────────┘
    │                     │
    │◀────VETO───────────┘
    ▼
Tool Execution (if approved)
```

---

## Code Examples Structure

Each topic includes implementations in three formats:

### Pseudo-code
For understanding the pattern without framework specifics.

```
function react_loop(task):
    while not task.complete:
        thought = llm.think(task, observations)
        action = llm.select_action(thought)
        observation = execute(action)
        observations.append(observation)
    return observations.final_answer
```

### Python (LangChain/LangGraph)

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")
tools = [search_tool, calculator_tool]

agent = create_react_agent(llm, tools)
result = agent.invoke({"messages": [("user", task)]})
```

### C# (Microsoft Agent Framework)

```csharp
using Microsoft.Extensions.AI;

var agent = new ChatAgent(
    new AzureOpenAIChatClient(endpoint, credential, "gpt-4"),
    new ChatAgentOptions { Instructions = "You are a helpful assistant." }
);

agent.Tools.Add(AIFunctionFactory.Create(SearchWeb));
var response = await agent.RunAsync("Find information about...");
```

---

## Model Benchmarks (DGX Spark Lab)

### Test Environment

- **Hardware:** NVIDIA DGX Spark (128GB unified memory)
- **Inference:** vLLM / Ollama
- **Models tested:** See below

### Models Under Evaluation

| Model | Parameters | Active | Memory (Q4) | Specialty |
|-------|------------|--------|-------------|-----------|
| gpt-oss:20b | 21B | 3.6B | ~16GB | Reasoning, tool use (baseline) |
| gpt-oss:120b | 117B | — | ~70GB | Larger GPT comparison |
| Nemotron-3-Nano | 30B | 3.2B | ~12GB | Agentic, 1M context claim |
| GLM-4.7-Flash | 30B | 3B | ~16GB | Coding, tool use, 200K context |
| Qwen3-Coder-30B-A3B | 30B | 3B | ~12GB | Agentic coding, tool calling |
| DeepSeek-V3.2 | 671B | MoE | ~TBD | Best open-source reasoning + tool use |
| MiMo-V2-Flash | 309B | 15B | ~TBD | Ultra-fast, 73.4% SWE-bench, 256K context |

**Note:** DeepSeek-V3.2 and MiMo-V2-Flash are large MoE models. Memory requirements depend on quantization and may require offloading strategies on DGX Spark.

### Evaluation Categories

#### Per-Topic Evaluations
Each topic has specific evaluation criteria:

| Topic | Evaluation Method | Key Metric |
|-------|-------------------|------------|
| Tool Calling | Function execution accuracy | % correct tool + args |
| Context Bloat | Needle-in-haystack at sizes | Recall degradation curve |
| Skills Discovery | Tool selection from filesystem | Precision@K |
| ReAct Pattern | Multi-step task completion | Success rate + steps |
| Memory Systems | Information retention | Recall after N turns |

#### Multi-Model Experiments
Unique to high-memory systems — run multiple models simultaneously:

```
Experiment: Supervisor-Worker Architecture
- Supervisor: Nemotron-3-Nano (planning, 1M context)
- Worker 1: gpt-oss:20b (code execution)
- Worker 2: GLM-4.7-Flash (coding tasks)
- Evaluator: Qwen3-Coder-30B-A3B (quality assessment)

Metrics: Task completion, coordination overhead, total latency
```

### Results Format

Results published as static JSON, rendered on website:

```json
{
  "experiment": "tool-calling-accuracy",
  "date": "2026-01-24",
  "models": [
    {
      "name": "gpt-oss:20b",
      "accuracy": 0.847,
      "latency_ms": 234,
      "tokens_per_second": 45.2
    },
    {
      "name": "nemotron-nano",
      "accuracy": 0.862,
      "latency_ms": 189,
      "tokens_per_second": 67.8
    }
  ],
  "methodology": "100 tool-calling tasks from ToolBench subset",
  "hardware": "DGX Spark, vLLM 0.12"
}
```

---

## Website Architecture

```
ai-agents-hub/
├── index.html                    # Main navigation
├── topics/
│   ├── tool-use/
│   │   ├── index.md             # Concept explanation
│   │   ├── examples.md          # Code in 3 formats
│   │   └── evaluation.md        # How to measure
│   ├── context-engineering/
│   ├── skills-pattern/
│   ├── protocols/
│   ├── learning-adaptation/
│   ├── multi-agent/
│   ├── agentic-rag/
│   ├── evaluation/
│   └── guardrails/
├── benchmarks/
│   ├── methodology.md            # Hardware setup & evaluation approach
│   ├── results/
│   │   └── *.json                # Static result files
│   └── dashboard.html            # Results visualization
└── resources/
    ├── papers.md                 # Research references
    └── frameworks.md             # Framework comparison
```

**Note:** Experiments are run offline on the DGX Spark and results are published as static JSON files. This keeps hardware resources private while providing transparent, reproducible benchmark data.

---

## Contributing

This is a living document. Key areas for contribution:
- Additional code examples
- New evaluation datasets
- Benchmark results from different hardware
- Corrections and clarifications

---

## References

### Research Papers
- ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., 2022)
- Reflexion: Language Agents with Verbal Reinforcement Learning (Shinn et al., 2023)
- MemGPT: Towards LLMs as Operating Systems (Packer et al., 2023)
- Graph RAG (Microsoft Research, 2024)

### Frameworks & Tools
- LangChain/LangGraph: https://langchain.com
- Microsoft Agent Framework: https://github.com/microsoft/agent-framework
- DeepEval: https://github.com/confident-ai/deepeval
- Anthropic Skills: https://github.com/anthropics/skills

### Protocols
- MCP (Model Context Protocol): https://modelcontextprotocol.io
- A2A (Agent2Agent): https://google.github.io/A2A

---

## License

Content is available under CC BY-SA 4.0. Code examples under MIT License.

---

*Last updated: January 2026*
