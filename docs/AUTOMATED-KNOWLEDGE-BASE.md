# Automated Knowledge Base

A plan for building a fully automated, self-updating knowledge base for agent engineering topics with deep dive capabilities.

## Vision

The site automatically:
1. Searches the web daily for AI agent news, papers, and developments
2. Performs weekly deep dives into papers, articles, and video content
3. Uses LLMs to read, analyze, and extract knowledge
4. Updates page content with new information
5. Pushes changes to git (via PR or direct commit)

## Current State

- Static Astro site deployed on Vercel
- GitHub Actions workflow for daily news updates (`update-news.yml`)
- RSS feed aggregation with Claude filtering
- Auto-commit to trigger rebuilds

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DAILY SCAN (GitHub Actions)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCOUT AGENT - Broad discovery, lightweight processing                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Tavily Search ──┬── "AI agents" "LLM tools" "MCP"                 │   │
│  │                  ├── "LangChain" "AutoGen" "CrewAI"                │   │
│  │                  └── "agent frameworks 2025"                        │   │
│  │                                                                     │   │
│  │  arXiv API ──────── cs.AI, cs.CL, cs.LG (last 24h)                 │   │
│  │                                                                     │   │
│  │  GitHub API ─────── Trending repos: agents, llm, ai                │   │
│  │                                                                     │   │
│  │  YouTube Search ─── AI agent channels, new uploads                  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│                    src/data/research/YYYY-MM-DD.json                        │
│                    (titles, URLs, summaries, relevance scores)              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WEEKLY DEEP DIVE - TIERED LLM PROCESSING                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TIER 1: BULK PROCESSING (Together API - Cheap Model)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Model: Llama 3.3 70B or DeepSeek-R1 via Together API               │   │
│  │  Cost: ~$0.20/million tokens (vs Claude $3-15/million)              │   │
│  │                                                                     │   │
│  │  Process ALL week's findings (~30-50 items):                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   PAPERS    │  │  ARTICLES   │  │   VIDEOS    │                 │   │
│  │  ├─────────────┤  ├─────────────┤  ├─────────────┤                 │   │
│  │  │ Extract:    │  │ Extract:    │  │ Extract:    │                 │   │
│  │  │ • Summary   │  │ • Summary   │  │ • Summary   │                 │   │
│  │  │ • Key ideas │  │ • Key ideas │  │ • Key ideas │                 │   │
│  │  │ • Relevance │  │ • Relevance │  │ • Relevance │                 │   │
│  │  │   score 1-10│  │   score 1-10│  │   score 1-10│                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  │                                                                     │   │
│  │  Output: Ranked list with scores + rough summaries                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                          Filter: score >= 7                                 │
│                                    │                                        │
│                                    ▼                                        │
│  TIER 2: QUALITY ANALYSIS (Claude - Premium Model)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Model: Claude Sonnet/Opus                                          │   │
│  │  Process only TOP 5-10 high-ranked items                            │   │
│  │                                                                     │   │
│  │  Deep analysis:                                                     │   │
│  │  • Detailed summaries with nuance                                   │   │
│  │  • Code extraction and reconstruction                               │   │
│  │  • Site integration suggestions                                     │   │
│  │  • Quality writing for content updates                              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│                    src/data/deep-dives/YYYY-WW.json                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONTENT AGENT (Weekly)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Compare deep dive findings with existing site content                       │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  LOW RISK (Auto-merge)          │  HIGH RISK (Create PR)            │  │
│  │  ─────────────────────          │  ────────────────────             │  │
│  │  • New resource links           │  • Topic page changes             │  │
│  │  • News items                   │  • New code examples              │  │
│  │  • Benchmark updates            │  • New sections                   │  │
│  │  • Tool version updates         │  • Architectural changes          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tiered LLM Strategy

The key cost optimization: use **cheap open-source models** for bulk processing, **Claude only for the best content**.

### Why This Works

| Task | Cheap Model (Together) | Premium Model (Claude) |
|------|------------------------|------------------------|
| Summarization | ✅ Good enough | Overkill |
| Relevance scoring | ✅ Good enough | Overkill |
| Code extraction | ⚠️ Decent | ✅ Better |
| Nuanced analysis | ❌ Misses subtlety | ✅ Required |
| Content writing | ❌ Generic | ✅ Required |

### Model Options (Together API)

| Model | Cost (per 1M tokens) | Quality | Best For |
|-------|---------------------|---------|----------|
| **Llama 3.3 70B** | $0.88 in / $0.88 out | Very good | General analysis |
| **DeepSeek-R1** | $0.55 in / $2.19 out | Excellent reasoning | Complex papers |
| **Qwen 2.5 72B** | $0.90 in / $0.90 out | Very good | Multilingual |
| **Mistral Large** | $2.00 in / $6.00 out | Great | Fallback |

**Recommendation:** Llama 3.3 70B for bulk processing - best quality/cost ratio.

### Together API Integration

```python
from together import Together

client = Together(api_key=os.environ["TOGETHER_API_KEY"])

def bulk_analyze(content: str, content_type: str) -> dict:
    """Tier 1: Cheap model for initial analysis and ranking."""

    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[{
            "role": "user",
            "content": f"""Analyze this {content_type} about AI agents.

{content[:15000]}  # Truncate to manage costs

Return JSON:
{{
    "summary": "2-3 sentence summary",
    "key_ideas": ["idea1", "idea2", "idea3"],
    "relevance_score": 1-10,
    "topics": ["topic1", "topic2"],
    "has_code": true/false,
    "novelty": "high/medium/low",
    "recommend_deep_dive": true/false
}}"""
        }],
        temperature=0.3,
        max_tokens=500
    )

    return json.loads(response.choices[0].message.content)


def deep_analyze_with_claude(content: str, bulk_analysis: dict) -> dict:
    """Tier 2: Claude for high-quality analysis of top content."""

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""You're analyzing high-value content for an AI agents knowledge base.

Previous analysis flagged this as highly relevant:
{json.dumps(bulk_analysis, indent=2)}

Full content:
{content}

Provide detailed analysis:
1. **Key Contribution**: What's genuinely new here?
2. **Technical Details**: Extract any code, algorithms, or techniques
3. **Practical Application**: How can agent builders use this?
4. **Site Integration**: Which topic pages should be updated?
5. **Content Draft**: Write 2-3 paragraphs ready to add to our site
"""
        }]
    )

    return parse_claude_response(response)
```

### Processing Pipeline

```python
def weekly_deep_dive():
    # 1. Collect week's findings
    findings = collect_week_findings()  # ~30-50 items

    # 2. TIER 1: Bulk process ALL with cheap model
    bulk_results = []
    for item in findings:
        content = fetch_full_content(item)  # PDF, transcript, article
        analysis = bulk_analyze(content, item['type'])
        bulk_results.append({**item, **analysis})

    # Cost: ~50 items × 10K tokens × $0.88/1M = ~$0.44

    # 3. Filter to high-value items
    top_items = [r for r in bulk_results if r['relevance_score'] >= 7]
    top_items = sorted(top_items, key=lambda x: x['relevance_score'], reverse=True)[:10]

    # 4. TIER 2: Deep dive with Claude on TOP items only
    deep_results = []
    for item in top_items:
        content = fetch_full_content(item)
        deep_analysis = deep_analyze_with_claude(content, item)
        deep_results.append({**item, 'deep_dive': deep_analysis})

    # Cost: ~10 items × 15K tokens × $3/1M = ~$0.45

    # 5. Save results
    save_deep_dive(deep_results)

    # Total weekly cost: ~$0.90 (vs ~$4.50 with Claude-only)
```

## Content Sources

### Primary: Tavily Search API
- **Why Tavily**: Built for AI agents, returns clean extracted content, handles JavaScript-rendered pages
- **Cost**: $5/month for 1000 searches (sufficient for daily + deep dives)
- **Usage**: 5-10 queries/day for discovery, content extraction for deep dives

### Papers: arXiv
```python
import arxiv

# Free, no API key required
search = arxiv.Search(
    query="cat:cs.AI AND (agents OR LLM OR tools)",
    max_results=20,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

for paper in search.results():
    # Download PDF, extract text with pypdf
    paper.download_pdf(filename=f"{paper.get_short_id()}.pdf")
```

### Videos: YouTube Transcripts
```python
from youtube_transcript_api import YouTubeTranscriptApi

# Free, no API key required
# Works with auto-generated and manual captions
transcript = YouTubeTranscriptApi.get_transcript(video_id)
full_text = " ".join([segment['text'] for segment in transcript])

# Typical 30-min video = ~5000 words = ~6000 tokens
# Claude analysis cost: ~$0.02-0.05 per video
```

**Target Channels:**
- AI Explained, Yannic Kilcher, Two Minute Papers
- Anthropic, OpenAI, Google DeepMind official channels
- LangChain, LlamaIndex community channels

### GitHub Trending
```python
import requests

# No auth required for basic trending
response = requests.get(
    "https://api.github.com/search/repositories",
    params={
        "q": "topic:ai-agents created:>2025-01-01",
        "sort": "stars",
        "order": "desc"
    }
)
```

## Implementation Phases

### Phase 1: Scout Agent (Week 1-2)

**Goal:** Daily discovery across all sources

**New Script:** `scripts/scout-agent.py`
```python
"""
Daily scout that discovers new content across sources.
Runs in ~2 minutes, costs ~$0.10/day
"""

from tavily import TavilyClient
import arxiv
from youtube_transcript_api import YouTubeTranscriptApi
import json
from datetime import datetime

def scout():
    findings = []

    # 1. Tavily web search
    tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    for query in QUERIES:
        results = tavily.search(query, max_results=5)
        findings.extend(process_tavily(results))

    # 2. arXiv papers (last 24h)
    findings.extend(fetch_arxiv_recent())

    # 3. YouTube (check subscribed channels)
    findings.extend(check_youtube_channels())

    # 4. GitHub trending
    findings.extend(fetch_github_trending())

    # 5. Score and dedupe
    scored = score_relevance(findings)

    # 6. Save
    save_research(scored)

QUERIES = [
    "AI agents framework 2025",
    "MCP model context protocol",
    "LangGraph tutorial",
    "autonomous agents LLM",
    "agent orchestration patterns",
]
```

**Tasks:**
- [ ] Set up Tavily API integration
- [ ] Add arXiv paper discovery
- [ ] Add YouTube channel monitoring
- [ ] Add GitHub trending detection
- [ ] Create relevance scoring with Claude
- [ ] Store daily findings in `src/data/research/`

**Output Format:**
```json
{
  "date": "2025-01-31",
  "stats": {
    "sources_checked": 4,
    "items_found": 47,
    "items_relevant": 12
  },
  "findings": [
    {
      "id": "arxiv-2501.12345",
      "type": "paper",
      "title": "ReAct Agents with Long-Term Memory",
      "url": "https://arxiv.org/abs/2501.12345",
      "source": "arxiv",
      "summary": "Proposes a new memory architecture...",
      "relevance_score": 0.94,
      "topics": ["memory", "react-pattern"],
      "deep_dive_priority": "high"
    },
    {
      "id": "yt-abc123",
      "type": "video",
      "title": "Building Production AI Agents",
      "url": "https://youtube.com/watch?v=abc123",
      "source": "youtube",
      "channel": "AI Explained",
      "duration_minutes": 24,
      "summary": "Walkthrough of production deployment...",
      "relevance_score": 0.87,
      "topics": ["deployment", "production"],
      "deep_dive_priority": "medium"
    }
  ]
}
```

### Phase 2: Deep Dive Engine (Week 3-4)

**Goal:** Weekly deep analysis of top discoveries

**New Script:** `scripts/deep-dive-agent.py`
```python
"""
Weekly deep dive into top content.
Runs ~30 minutes, costs ~$2-5/week
"""

def deep_dive():
    # 1. Collect week's findings
    week_findings = collect_week_findings()

    # 2. Rank by priority
    top_items = rank_for_deep_dive(week_findings, limit=10)

    # 3. Process each item
    analyses = []
    for item in top_items:
        if item['type'] == 'paper':
            analysis = analyze_paper(item)
        elif item['type'] == 'video':
            analysis = analyze_video(item)
        elif item['type'] == 'article':
            analysis = analyze_article(item)
        analyses.append(analysis)

    # 4. Save deep dive results
    save_deep_dive(analyses)

def analyze_paper(item):
    """Download PDF, extract text, analyze with Claude."""
    pdf_path = download_arxiv_pdf(item['url'])
    text = extract_pdf_text(pdf_path)

    analysis = claude_analyze(text, prompt="""
        Analyze this AI research paper. Extract:
        1. Key contribution (2-3 sentences)
        2. Novel techniques introduced
        3. Relevant code/pseudocode
        4. How this relates to: {SITE_TOPICS}
        5. Practical applications for agent builders
    """)
    return analysis

def analyze_video(item):
    """Get transcript, analyze with Claude."""
    transcript = get_youtube_transcript(item['url'])

    analysis = claude_analyze(transcript, prompt="""
        Analyze this video transcript about AI agents. Extract:
        1. Main topic and key points
        2. Tools/frameworks demonstrated
        3. Code examples shown (reconstruct if described verbally)
        4. Practical tips mentioned
        5. Links/resources mentioned
    """)
    return analysis
```

**Tasks:**
- [ ] Create PDF text extraction pipeline
- [ ] Create YouTube transcript pipeline
- [ ] Create article full-text extraction
- [ ] Design Claude analysis prompts
- [ ] Implement priority ranking algorithm
- [ ] Store deep dive results

**Deep Dive Output Format:**
```json
{
  "week": "2025-W05",
  "processed": 10,
  "analyses": [
    {
      "id": "arxiv-2501.12345",
      "type": "paper",
      "title": "ReAct Agents with Long-Term Memory",
      "deep_dive": {
        "key_contribution": "Novel memory architecture that allows...",
        "techniques": [
          {
            "name": "Hierarchical Memory Bank",
            "description": "Three-tier memory system..."
          }
        ],
        "code_snippets": [
          {
            "language": "python",
            "description": "Memory retrieval function",
            "code": "def retrieve_memory(query, k=5):..."
          }
        ],
        "site_relevance": {
          "topics": ["memory", "react-pattern"],
          "suggested_updates": [
            {
              "page": "/topics/memory/",
              "section": "Long-term Memory",
              "suggestion": "Add section on hierarchical memory banks"
            }
          ]
        }
      },
      "tokens_used": 15000,
      "cost_usd": 0.23
    }
  ]
}
```

### Phase 3: Auto-Update Resources (Week 5-6)

**Goal:** Automatically add new tools, papers, and links

**Tasks:**
- [ ] Create `scripts/update-resources.py`
- [ ] Parse existing resources to avoid duplicates
- [ ] Auto-categorize (papers, tools, frameworks, tutorials)
- [ ] Auto-commit with source attribution

### Phase 4: Content Suggestions (Week 7-8)

**Goal:** Generate PRs for topic page updates

**Tasks:**
- [ ] Create `scripts/content-agent.py`
- [ ] Compare deep dive findings with existing content
- [ ] Generate markdown diffs
- [ ] Create PRs with full context

**PR Template:**
```markdown
## Auto-generated Content Update

**Source:** [Paper Title](https://arxiv.org/abs/...)
**Confidence:** 0.87
**Topics affected:** memory, react-pattern

### Suggested Changes

#### `/topics/memory/index.astro`

Add new section after "Short-term Memory":

```astro
## Hierarchical Memory Banks

Recent research (Smith et al., 2025) introduces a three-tier memory architecture...
```

### Why this matters
This paper introduces a novel approach that directly relates to our memory topic...

---
*Generated by deep-dive-agent on 2025-02-01*
```

## Python Dependencies

```txt
# requirements.txt
anthropic>=0.18.0
together>=1.0.0
tavily-python>=0.3.0
arxiv>=2.1.0
pypdf>=4.0.0
youtube-transcript-api>=0.6.0
requests>=2.31.0
```

## GitHub Secrets Required

| Secret | Purpose |
|--------|---------|
| `ANTHROPIC_API_KEY` | Claude API for premium analysis (Tier 2) |
| `TOGETHER_API_KEY` | Together API for bulk processing (Tier 1) |
| `TAVILY_API_KEY` | Web search and extraction |
| `GITHUB_TOKEN` | Auto-provided for PRs |

## Workflow Schedule

```yaml
# .github/workflows/scout.yml
on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8am UTC
  workflow_dispatch:

# .github/workflows/deep-dive.yml
on:
  schedule:
    - cron: '0 10 * * 0'  # Weekly on Sunday at 10am UTC
  workflow_dispatch:
```

## Cost Estimate

### With Tiered LLM Strategy (Recommended)

| Service | Daily | Weekly | Monthly |
|---------|-------|--------|---------|
| **Tavily** | $0.05 | - | ~$1.50 |
| **Together API (Tier 1 bulk)** | - | $0.50 | ~$2 |
| **Claude (Tier 2 premium)** | - | $0.50 | ~$2 |
| **Vercel** | - | - | Free |
| **Total** | | | **~$6-8/mo** |

### Cost Breakdown

```
Weekly processing:
├── Tier 1: 50 items × 10K tokens × $0.88/1M = $0.44
├── Tier 2: 10 items × 15K tokens × $3/1M   = $0.45
└── Tavily: 35 queries × $0.005             = $0.18
                                      Total = ~$1.07/week
```

### Comparison: Old vs New

| Approach | Monthly Cost | Quality |
|----------|--------------|---------|
| Claude-only (old plan) | $20-25 | Overkill for bulk |
| **Tiered (new plan)** | **$6-8** | Right model for each task |
| Together-only | $3-4 | Misses nuance on best content |

### With Optional Add-ons

| Add-on | Additional Cost |
|--------|-----------------|
| Podcast transcription (Whisper) | +$5-10/mo |
| More deep dives (20/week) | +$2/mo |
| Daily Claude summaries | +$3/mo |

## File Structure

```
agent-engineering/
├── .github/
│   └── workflows/
│       ├── update-news.yml         # Existing RSS
│       ├── scout.yml               # Daily discovery
│       ├── deep-dive.yml           # Weekly analysis
│       └── content-update.yml      # Weekly PRs
├── scripts/
│   ├── update-news.py              # Existing
│   ├── scout-agent.py              # Phase 1
│   ├── deep-dive-agent.py          # Phase 2
│   ├── update-resources.py         # Phase 3
│   └── content-agent.py            # Phase 4
├── src/
│   └── data/
│       ├── news.json               # Existing
│       ├── resources.json          # Auto-updated
│       ├── research/               # Daily scout findings
│       │   └── YYYY-MM-DD.json
│       └── deep-dives/             # Weekly analyses
│           └── YYYY-WW.json
└── docs/
    └── AUTOMATED-KNOWLEDGE-BASE.md
```

## Safety Guardrails

1. **Never auto-delete content** - Only additions and modifications
2. **Source attribution** - Always link to original sources
3. **Confidence thresholds** - Only apply changes above 0.8 confidence
4. **Human review for content** - PRs for any topic page changes
5. **Rate limiting** - Max 50 Tavily queries/day, 10 deep dives/week
6. **Cost caps** - Alert if daily spend > $1 or weekly > $10
7. **Dry-run mode** - Test changes without committing
8. **Rollback capability** - Git history allows easy revert

## Quality Filters

### Video Selection Criteria
- Channel subscriber count > 10,000
- Video has captions available
- Duration between 5-60 minutes
- Published within last 7 days
- Title contains relevant keywords

### Paper Selection Criteria
- Published on arXiv in cs.AI, cs.CL, cs.LG
- Abstract mentions: agent, tool, LLM, reasoning
- Has code repository linked (bonus)

### Article Selection Criteria
- From known quality sources (official blogs, reputable tech sites)
- Published within last 7 days
- Word count > 500

## Monitoring & Alerts

- **GitHub Actions logs** for debugging
- **Cost tracking** in daily summary JSON
- **Weekly digest** PR comment with stats
- **Failure alerts** via GitHub Actions notifications

## Getting Started

1. **Get API Keys**
   ```bash
   # Tavily - https://tavily.com (search)
   # Together - https://together.ai (cheap bulk LLM)
   # Anthropic - https://console.anthropic.com (premium LLM)

   # Add to GitHub Secrets:
   # - TAVILY_API_KEY
   # - TOGETHER_API_KEY
   # - ANTHROPIC_API_KEY
   ```

2. **Test Scout Locally**
   ```bash
   export ANTHROPIC_API_KEY=your-key
   export TOGETHER_API_KEY=your-key
   export TAVILY_API_KEY=your-key
   python scripts/scout-agent.py --dry-run
   ```

3. **Test Tiered Deep Dive Locally**
   ```bash
   # Test Tier 1 only (bulk processing)
   python scripts/deep-dive-agent.py --tier1-only --limit 5

   # Test full pipeline
   python scripts/deep-dive-agent.py --limit 2 --dry-run
   ```

4. **Enable Workflows**
   ```bash
   # Uncomment schedule triggers in workflow files
   git push
   ```

## Future Enhancements

- **Podcast transcription** - Whisper API for audio content
- **Conference tracking** - Monitor NeurIPS, ICML, ACL proceedings
- **Community signals** - Reddit, HN, Twitter/X trending
- **Multi-language** - Auto-translate non-English papers
- **Interactive dashboard** - View research pipeline status
- **Slack/Discord bot** - Get notified of high-priority findings

## References

- [Together API Docs](https://docs.together.ai/)
- [Together Models List](https://docs.together.ai/docs/inference-models)
- [Tavily API Docs](https://docs.tavily.com/)
- [arXiv API](https://info.arxiv.org/help/api/index.html)
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Anthropic Claude API](https://docs.anthropic.com/)
