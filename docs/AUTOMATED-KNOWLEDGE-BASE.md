# Automated Knowledge Base

A plan for building a fully automated, self-updating knowledge base for agent engineering topics.

## Vision

The site automatically:
1. Searches the web daily for AI agent news, papers, and developments
2. Uses LLMs to read, analyze, and extract knowledge
3. Updates page content with new information
4. Pushes changes to git (via PR or direct commit)

## Current State

- Static Astro site deployed on Vercel
- GitHub Actions workflow for daily news updates (`update-news.yml`)
- RSS feed aggregation with Claude filtering
- Auto-commit to trigger rebuilds

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Daily Cron (GitHub Actions)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. RESEARCH AGENT                                              │
│     │                                                           │
│     ├── Web Search                                              │
│     │   └── Query: "AI agents" "LLM tools" "MCP" etc.          │
│     │                                                           │
│     ├── Source APIs                                             │
│     │   ├── Tavily Search API (AI-optimized)                   │
│     │   ├── Brave Search API (free tier available)             │
│     │   ├── arXiv API (papers)                                 │
│     │   └── GitHub API (trending repos)                        │
│     │                                                           │
│     └── Output: src/data/research/YYYY-MM-DD.json              │
│                                                                 │
│  2. ANALYSIS AGENT                                              │
│     │                                                           │
│     ├── Compare new findings with existing content             │
│     ├── Identify:                                              │
│     │   ├── New tools/frameworks                               │
│     │   ├── Updated benchmarks                                 │
│     │   ├── New patterns/techniques                            │
│     │   └── Breaking news                                      │
│     │                                                           │
│     └── Output: src/data/suggestions.json                      │
│                                                                 │
│  3. CONTENT AGENT                                               │
│     │                                                           │
│     ├── Low-risk updates (auto-merge)                          │
│     │   ├── New resources/links                                │
│     │   ├── Benchmark score updates                            │
│     │   └── News items                                         │
│     │                                                           │
│     ├── High-risk updates (PR for review)                      │
│     │   ├── Topic page content changes                         │
│     │   ├── New sections                                       │
│     │   └── Architectural changes                              │
│     │                                                           │
│     └── Output: Git commit or Pull Request                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Enhanced Research (Week 1-2)

**Goal:** Expand beyond RSS feeds to active web search

**Tasks:**
- [ ] Add Tavily or Brave Search API integration
- [ ] Create research agent script (`scripts/research-agent.py`)
- [ ] Store daily research in `src/data/research/`
- [ ] Update news workflow to include web search results

**New Files:**
```
scripts/
├── research-agent.py      # Web search + content extraction
├── requirements.txt       # Add tavily-python or brave-search
src/data/
├── research/
│   └── YYYY-MM-DD.json   # Daily research findings
```

**Sample Research Output:**
```json
{
  "date": "2025-01-31",
  "queries": ["AI agents 2025", "MCP protocol updates", "LangChain news"],
  "findings": [
    {
      "title": "New MCP Feature Released",
      "url": "https://...",
      "summary": "...",
      "relevance_score": 0.92,
      "topics": ["mcp", "protocols"],
      "type": "news"
    }
  ]
}
```

### Phase 2: Auto-Update Resources (Week 3-4)

**Goal:** Automatically add new tools, papers, and links to resources page

**Tasks:**
- [ ] Create content updater script (`scripts/update-resources.py`)
- [ ] Parse existing resources to avoid duplicates
- [ ] Categorize new findings (papers, tools, frameworks)
- [ ] Auto-commit resource updates

**Update Workflow:**
```yaml
- name: Update resources
  run: python scripts/update-resources.py
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

- name: Commit resource updates
  run: |
    git add src/data/resources.json
    git commit -m "Auto-update resources $(date +%Y-%m-%d)" || exit 0
    git push
```

### Phase 3: Content Suggestions (Week 5-6)

**Goal:** Generate suggested updates for topic pages

**Tasks:**
- [ ] Create analysis agent (`scripts/analysis-agent.py`)
- [ ] Compare research findings with existing topic content
- [ ] Generate markdown diffs for suggested changes
- [ ] Create PRs for human review

**Suggestion Format:**
```json
{
  "date": "2025-01-31",
  "suggestions": [
    {
      "page": "/topics/mcp/",
      "section": "New Features",
      "type": "addition",
      "content": "## Streamable HTTP Transport\n\nAs of January 2025...",
      "sources": ["https://..."],
      "confidence": 0.85
    }
  ]
}
```

### Phase 4: Automated Content Updates (Week 7-8)

**Goal:** Auto-merge low-risk updates, PR for high-risk

**Risk Classification:**
| Update Type | Risk Level | Action |
|-------------|------------|--------|
| New resource link | Low | Auto-merge |
| Benchmark score | Low | Auto-merge |
| News item | Low | Auto-merge |
| New code example | Medium | PR |
| Topic content change | High | PR |
| New topic page | High | PR |

**Tasks:**
- [ ] Create content agent (`scripts/content-agent.py`)
- [ ] Implement risk classification
- [ ] Auto-merge low-risk via direct commit
- [ ] Create PRs for medium/high risk via `gh pr create`

## API Requirements

### Search APIs (choose one or more)

| API | Cost | Pros | Cons |
|-----|------|------|------|
| **Tavily** | $5/mo (1000 searches) | Built for AI, returns clean content | Paid |
| **Brave Search** | Free tier (2000/mo) | Good quality, free tier | Rate limited |
| **SerpAPI** | $50/mo | Google results | Expensive |
| **Bing Search** | $3/1000 queries | Microsoft ecosystem | Azure setup |

**Recommendation:** Start with Brave Search (free), upgrade to Tavily if needed.

### LLM API

- **Anthropic Claude** (already configured)
- Estimated usage: ~$10-20/mo for daily research + analysis

### GitHub API

- Already available via `GITHUB_TOKEN` in Actions
- Used for creating PRs

## Cost Estimate

| Service | Monthly Cost |
|---------|--------------|
| Brave Search API | Free (2000 queries) |
| Anthropic Claude | $10-20 |
| Vercel Hosting | Free |
| **Total** | **~$10-20/mo** |

With Tavily instead of Brave: **~$15-25/mo**

## File Structure (Final)

```
agent-engineering/
├── .github/
│   └── workflows/
│       ├── update-news.yml          # Existing
│       ├── research.yml             # Daily research
│       └── content-update.yml       # Weekly content updates
├── scripts/
│   ├── update-news.py               # Existing
│   ├── research-agent.py            # Phase 1
│   ├── update-resources.py          # Phase 2
│   ├── analysis-agent.py            # Phase 3
│   └── content-agent.py             # Phase 4
├── src/
│   └── data/
│       ├── news.json                # Existing
│       ├── resources.json           # Auto-updated resources
│       ├── research/                # Daily research findings
│       │   └── YYYY-MM-DD.json
│       └── suggestions/             # Content suggestions
│           └── YYYY-MM-DD.json
└── docs/
    └── AUTOMATED-KNOWLEDGE-BASE.md  # This file
```

## Safety Guardrails

1. **Never auto-delete content** - Only additions and modifications
2. **Source attribution** - Always link to original sources
3. **Confidence thresholds** - Only apply changes above 0.8 confidence
4. **Human review for content** - PRs for any topic page changes
5. **Rate limiting** - Max 100 API calls per day
6. **Rollback capability** - Git history allows easy revert
7. **Dry-run mode** - Test changes without committing

## Monitoring

- GitHub Actions logs for debugging
- Weekly summary email (optional)
- Vercel Analytics for traffic impact
- Cost alerts on API dashboards

## Future Enhancements

- **Slack/Discord notifications** for new findings
- **User submissions** - Form for suggesting topics
- **Multi-language support** - Auto-translate content
- **Audio/Video processing** - Summarize YouTube talks, podcasts
- **Research paper deep-dives** - Full arXiv paper analysis
- **Community contributions** - Auto-review external PRs

## Getting Started

1. **Set up Brave Search API**
   ```bash
   # Get free API key at https://brave.com/search/api/
   # Add to GitHub Secrets as BRAVE_API_KEY
   ```

2. **Run Phase 1 locally**
   ```bash
   export ANTHROPIC_API_KEY=your-key
   export BRAVE_API_KEY=your-key
   python scripts/research-agent.py
   ```

3. **Enable GitHub Action**
   ```yaml
   # Uncomment schedule in .github/workflows/research.yml
   ```

## References

- [Tavily API Docs](https://docs.tavily.com/)
- [Brave Search API](https://brave.com/search/api/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Anthropic Claude API](https://docs.anthropic.com/)
