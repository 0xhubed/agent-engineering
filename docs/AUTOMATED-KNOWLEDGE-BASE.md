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
│                       WEEKLY DEEP DIVE (GitHub Actions)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ANALYST AGENT - Deep processing of top discoveries                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  1. Rank week's findings by relevance + novelty                    │   │
│  │  2. Select top 10 items for deep dive                              │   │
│  │  3. Process by type:                                               │   │
│  │                                                                     │   │
│  │     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │     │   PAPERS    │  │  ARTICLES   │  │   VIDEOS    │              │   │
│  │     ├─────────────┤  ├─────────────┤  ├─────────────┤              │   │
│  │     │ arxiv lib   │  │ Tavily      │  │ youtube-    │              │   │
│  │     │ pypdf       │  │ extract     │  │ transcript  │              │   │
│  │     │ full text   │  │ full text   │  │ -api        │              │   │
│  │     ├─────────────┤  ├─────────────┤  ├─────────────┤              │   │
│  │     │ Claude:     │  │ Claude:     │  │ Claude:     │              │   │
│  │     │ - Summary   │  │ - Summary   │  │ - Summary   │              │   │
│  │     │ - Key ideas │  │ - Key ideas │  │ - Key ideas │              │   │
│  │     │ - Code      │  │ - Tools     │  │ - Demos     │              │   │
│  │     │   snippets  │  │   mentioned │  │   shown     │              │   │
│  │     └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│                    src/data/deep-dives/YYYY-WW.json                         │
│                    (full analysis, extracted knowledge)                     │
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
tavily-python>=0.3.0
arxiv>=2.1.0
pypdf>=4.0.0
youtube-transcript-api>=0.6.0
requests>=2.31.0
```

## GitHub Secrets Required

| Secret | Purpose |
|--------|---------|
| `ANTHROPIC_API_KEY` | Claude API for analysis |
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

| Service | Daily | Weekly | Monthly |
|---------|-------|--------|---------|
| **Tavily** | $0.05 | - | ~$1.50 |
| **Claude (scout)** | $0.10 | - | ~$3 |
| **Claude (deep dive)** | - | $3-5 | ~$15-20 |
| **Vercel** | - | - | Free |
| **Total** | | | **~$20-25/mo** |

With optional podcast transcription (Whisper): **~$30-40/mo**

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

1. **Get Tavily API Key**
   ```bash
   # Sign up at https://tavily.com
   # Add to GitHub Secrets as TAVILY_API_KEY
   ```

2. **Test Scout Locally**
   ```bash
   export ANTHROPIC_API_KEY=your-key
   export TAVILY_API_KEY=your-key
   python scripts/scout-agent.py --dry-run
   ```

3. **Test Deep Dive Locally**
   ```bash
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

- [Tavily API Docs](https://docs.tavily.com/)
- [arXiv API](https://info.arxiv.org/help/api/index.html)
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Anthropic Claude API](https://docs.anthropic.com/)
