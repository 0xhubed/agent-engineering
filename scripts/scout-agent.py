#!/usr/bin/env python3
"""
Scout Agent: Daily discovery agent for AI agent engineering research.

Searches multiple sources (Tavily, arXiv, YouTube, GitHub) and scores findings
using Together API for cost-effective bulk LLM processing.

Usage:
    python scripts/scout-agent.py [--dry-run] [--sources SOURCE1,SOURCE2]

Examples:
    python scripts/scout-agent.py --dry-run
    python scripts/scout-agent.py --sources arxiv,github
    python scripts/scout-agent.py
"""

import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import httpx

# =============================================================================
# Configuration
# =============================================================================

TOGETHER_MODEL = "togethercomputer/gpt-oss-120b"

# Tavily search queries
TAVILY_QUERIES = [
    "AI agents framework 2026",
    "MCP model context protocol",
    "LangGraph tutorial",
    "autonomous agents LLM",
    "agent orchestration patterns",
    "multi-agent systems AI",
    "ReAct agent pattern",
    "tool use LLM agents",
]

# YouTube channels to monitor (channel_id: name)
YOUTUBE_CHANNELS = {
    "UCbfYPyITQ-7l4upoX8nvctg": "Two Minute Papers",
    "UCWN3xxRkmTPmbKwht9FuE5A": "Yannic Kilcher",
    "UCZHmQk67mN3uuiNlm_Uo_Xw": "AI Explained",
}

# GitHub trending topics
GITHUB_TOPICS = ["ai-agents", "llm", "langchain", "autogen", "crewai"]

# arXiv categories to search
ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG"]

# Relevance topics for scoring
RELEVANCE_TOPICS = [
    "tool-use",
    "react-pattern",
    "memory",
    "multi-agent",
    "mcp",
    "orchestration",
    "rag",
    "evaluation",
    "guardrails",
    "planning",
]

# =============================================================================
# Source Fetchers
# =============================================================================


def fetch_tavily(api_key: str, dry_run: bool = False) -> list[dict]:
    """Fetch results from Tavily search API."""
    if dry_run:
        print("  [DRY-RUN] Would search Tavily with 8 queries")
        return [
            {
                "id": "tavily-dry-run-1",
                "type": "article",
                "title": "[DRY-RUN] Example Tavily Result",
                "url": "https://example.com/tavily-result",
                "source": "tavily",
                "summary": "This is a dry-run placeholder for Tavily results.",
                "raw_metadata": {"query": "AI agents framework 2026"},
            }
        ]

    items = []
    seen_urls = set()

    for query in TAVILY_QUERIES:
        try:
            response = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 5,
                    "include_answer": False,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            for result in data.get("results", []):
                url = result.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                items.append({
                    "id": f"tavily-{hashlib.md5(url.encode()).hexdigest()[:8]}",
                    "type": "article",
                    "title": result.get("title", ""),
                    "url": url,
                    "source": "tavily",
                    "summary": result.get("content", "")[:500],
                    "raw_metadata": {
                        "query": query,
                        "score": result.get("score"),
                    },
                })
        except Exception as e:
            print(f"  Warning: Tavily query '{query}' failed: {e}")
            continue

    return items


def fetch_arxiv(dry_run: bool = False) -> list[dict]:
    """Fetch recent papers from arXiv in AI-related categories."""
    if dry_run:
        print("  [DRY-RUN] Would fetch arXiv papers from cs.AI, cs.CL, cs.LG")
        return [
            {
                "id": "arxiv-dry-run-1",
                "type": "paper",
                "title": "[DRY-RUN] Example arXiv Paper",
                "url": "https://arxiv.org/abs/2601.00000",
                "source": "arxiv",
                "summary": "This is a dry-run placeholder for arXiv results.",
                "raw_metadata": {"categories": ["cs.AI"]},
            }
        ]

    items = []
    seen_ids = set()

    # Build query for multiple categories
    cat_query = " OR ".join([f"cat:{cat}" for cat in ARXIV_CATEGORIES])

    # Search for papers from the last 24 hours (use 3 days to be safe with timezones)
    try:
        # arXiv API query
        base_url = "https://export.arxiv.org/api/query"
        query = f"({cat_query}) AND (agent OR agents OR LLM OR \"language model\")"
        params = {
            "search_query": query,
            "start": 0,
            "max_results": 50,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        response = httpx.get(
            base_url,
            params=params,
            timeout=60,
            headers={"User-Agent": "AgentEngineering-Scout/1.0"},
        )
        response.raise_for_status()

        # Parse Atom feed
        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        cutoff = datetime.now() - timedelta(days=3)

        for entry in root.findall("atom:entry", ns):
            arxiv_id = entry.find("atom:id", ns)
            if arxiv_id is None:
                continue

            # Extract arXiv ID from URL
            arxiv_id_text = arxiv_id.text.split("/abs/")[-1] if arxiv_id.text else ""
            if arxiv_id_text in seen_ids:
                continue
            seen_ids.add(arxiv_id_text)

            # Parse published date
            published_elem = entry.find("atom:published", ns)
            if published_elem is not None and published_elem.text:
                try:
                    published = datetime.fromisoformat(published_elem.text.replace("Z", "+00:00"))
                    if published.replace(tzinfo=None) < cutoff:
                        continue
                except ValueError:
                    pass

            title_elem = entry.find("atom:title", ns)
            summary_elem = entry.find("atom:summary", ns)

            # Get categories
            categories = []
            for cat in entry.findall("arxiv:primary_category", ns):
                term = cat.get("term")
                if term:
                    categories.append(term)
            for cat in entry.findall("atom:category", ns):
                term = cat.get("term")
                if term and term not in categories:
                    categories.append(term)

            items.append({
                "id": f"arxiv-{arxiv_id_text}",
                "type": "paper",
                "title": (title_elem.text or "").strip().replace("\n", " "),
                "url": f"https://arxiv.org/abs/{arxiv_id_text}",
                "source": "arxiv",
                "summary": (summary_elem.text or "")[:500].strip().replace("\n", " "),
                "raw_metadata": {
                    "arxiv_id": arxiv_id_text,
                    "categories": categories,
                },
            })

    except Exception as e:
        print(f"  Warning: arXiv fetch failed: {e}")

    return items


def fetch_youtube(dry_run: bool = False) -> list[dict]:
    """Fetch recent videos from monitored YouTube channels via RSS."""
    if dry_run:
        print(f"  [DRY-RUN] Would fetch YouTube RSS for {len(YOUTUBE_CHANNELS)} channels")
        return [
            {
                "id": "youtube-dry-run-1",
                "type": "video",
                "title": "[DRY-RUN] Example YouTube Video",
                "url": "https://youtube.com/watch?v=example",
                "source": "youtube",
                "summary": "This is a dry-run placeholder for YouTube results.",
                "raw_metadata": {"channel": "Two Minute Papers"},
            }
        ]

    items = []
    seen_ids = set()
    cutoff = datetime.now() - timedelta(days=7)

    for channel_id, channel_name in YOUTUBE_CHANNELS.items():
        try:
            # YouTube RSS feed URL
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            response = httpx.get(
                feed_url,
                timeout=30,
                headers={"User-Agent": "AgentEngineering-Scout/1.0"},
            )
            response.raise_for_status()

            # Parse Atom feed
            root = ET.fromstring(response.text)
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "yt": "http://www.youtube.com/xml/schemas/2015",
                "media": "http://search.yahoo.com/mrss/",
            }

            for entry in root.findall("atom:entry", ns):
                video_id_elem = entry.find("yt:videoId", ns)
                if video_id_elem is None:
                    continue

                video_id = video_id_elem.text
                if video_id in seen_ids:
                    continue
                seen_ids.add(video_id)

                # Parse published date
                published_elem = entry.find("atom:published", ns)
                if published_elem is not None and published_elem.text:
                    try:
                        published = datetime.fromisoformat(published_elem.text.replace("Z", "+00:00"))
                        if published.replace(tzinfo=None) < cutoff:
                            continue
                    except ValueError:
                        pass

                title_elem = entry.find("atom:title", ns)
                media_group = entry.find("media:group", ns)
                description = ""
                if media_group is not None:
                    desc_elem = media_group.find("media:description", ns)
                    if desc_elem is not None:
                        description = (desc_elem.text or "")[:500]

                items.append({
                    "id": f"youtube-{video_id}",
                    "type": "video",
                    "title": (title_elem.text or "").strip(),
                    "url": f"https://youtube.com/watch?v={video_id}",
                    "source": "youtube",
                    "summary": description.strip(),
                    "raw_metadata": {
                        "video_id": video_id,
                        "channel": channel_name,
                        "channel_id": channel_id,
                    },
                })

        except Exception as e:
            print(f"  Warning: YouTube feed for {channel_name} failed: {e}")
            continue

    return items


def fetch_github_trending(dry_run: bool = False) -> list[dict]:
    """Fetch trending repositories from GitHub for relevant topics."""
    if dry_run:
        print(f"  [DRY-RUN] Would fetch GitHub trending for {len(GITHUB_TOPICS)} topics")
        return [
            {
                "id": "github-dry-run-1",
                "type": "repo",
                "title": "[DRY-RUN] example/repo",
                "url": "https://github.com/example/repo",
                "source": "github",
                "summary": "This is a dry-run placeholder for GitHub results.",
                "raw_metadata": {"topic": "ai-agents", "stars": 1000},
            }
        ]

    items = []
    seen_repos = set()

    # Calculate date for "created in last 30 days"
    since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    for topic in GITHUB_TOPICS:
        try:
            # GitHub search API
            query = f"topic:{topic} created:>{since_date}"
            response = httpx.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 10,
                },
                timeout=30,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "AgentEngineering-Scout/1.0",
                },
            )
            response.raise_for_status()
            data = response.json()

            for repo in data.get("items", []):
                full_name = repo.get("full_name", "")
                if full_name in seen_repos:
                    continue
                seen_repos.add(full_name)

                items.append({
                    "id": f"github-{full_name.replace('/', '-')}",
                    "type": "repo",
                    "title": full_name,
                    "url": repo.get("html_url", ""),
                    "source": "github",
                    "summary": (repo.get("description") or "")[:500],
                    "raw_metadata": {
                        "topic": topic,
                        "stars": repo.get("stargazers_count", 0),
                        "language": repo.get("language"),
                        "created_at": repo.get("created_at"),
                        "topics": repo.get("topics", []),
                    },
                })

        except Exception as e:
            print(f"  Warning: GitHub search for topic '{topic}' failed: {e}")
            continue

    return items


# =============================================================================
# Scoring with Together API
# =============================================================================


def score_items_with_together(items: list[dict], api_key: str, dry_run: bool = False) -> list[dict]:
    """Score items for relevance using Together API."""
    if not items:
        return []

    if dry_run:
        print(f"  [DRY-RUN] Would score {len(items)} items with Together API")
        # Return items with mock scores
        for item in items:
            item["relevance_score"] = 0.75
            item["topics"] = ["tool-use", "react-pattern"]
            item["deep_dive_priority"] = "medium"
        return items

    # Prepare batch prompt
    items_text = "\n\n".join([
        f"[{i}] {item['title']}\nType: {item['type']}\nSource: {item['source']}\nSummary: {item.get('summary', 'N/A')[:300]}"
        for i, item in enumerate(items)
    ])

    prompt = f"""You are an AI agent engineering research curator. Score each item for relevance to AI agent development.

Relevant topics include:
- Agent frameworks (LangChain, LangGraph, AutoGen, CrewAI, etc.)
- Agent patterns (ReAct, tool use, planning, memory systems)
- Multi-agent orchestration and coordination
- Agent protocols (MCP, A2A)
- RAG and retrieval for agents
- Agent evaluation and benchmarks
- Agent safety and guardrails
- LLM capabilities for agents

For each item, provide:
1. relevance_score: 0.0 to 1.0 (0.5+ is relevant)
2. topics: list of relevant tags from [{', '.join(RELEVANCE_TOPICS)}]
3. deep_dive_priority: "high", "medium", or "low" based on novelty and importance

ITEMS TO SCORE:
{items_text}

Respond in JSON format only:
{{
  "scores": [
    {{
      "index": 0,
      "relevance_score": 0.85,
      "topics": ["tool-use", "react-pattern"],
      "deep_dive_priority": "high"
    }}
  ]
}}"""

    try:
        response = httpx.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": TOGETHER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000,
                "temperature": 0.1,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        # Extract response text
        response_text = data["choices"][0]["message"]["content"]

        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())

        # Apply scores to items
        scored_items = []
        for score_info in result.get("scores", []):
            idx = score_info.get("index", -1)
            if 0 <= idx < len(items):
                item = items[idx].copy()
                item["relevance_score"] = score_info.get("relevance_score", 0.0)
                item["topics"] = score_info.get("topics", [])
                item["deep_dive_priority"] = score_info.get("deep_dive_priority", "low")
                scored_items.append(item)

        # Add any items that weren't scored (with default low score)
        scored_indices = {s.get("index") for s in result.get("scores", [])}
        for i, item in enumerate(items):
            if i not in scored_indices:
                item = item.copy()
                item["relevance_score"] = 0.0
                item["topics"] = []
                item["deep_dive_priority"] = "low"
                scored_items.append(item)

        return scored_items

    except json.JSONDecodeError as e:
        print(f"  Warning: Failed to parse Together API response: {e}")
        # Return items with default scores
        for item in items:
            item["relevance_score"] = 0.5
            item["topics"] = []
            item["deep_dive_priority"] = "low"
        return items
    except Exception as e:
        print(f"  Warning: Together API scoring failed: {e}")
        # Return items with default scores
        for item in items:
            item["relevance_score"] = 0.5
            item["topics"] = []
            item["deep_dive_priority"] = "low"
        return items


def estimate_tokens(items: list[dict]) -> int:
    """Estimate token count for scoring prompt."""
    # Rough estimate: ~4 chars per token
    text_length = sum(
        len(item.get("title", "")) + len(item.get("summary", ""))
        for item in items
    )
    # Add prompt overhead (~500 tokens)
    return (text_length // 4) + 500


def estimate_cost(tokens: int) -> float:
    """Estimate cost in USD for Together API usage."""
    # GPT-OSS 120B pricing: ~$0.0005 per 1K tokens (rough estimate)
    return (tokens / 1000) * 0.0005


# =============================================================================
# Main Logic
# =============================================================================


def validate_api_keys(sources: list[str], dry_run: bool) -> dict[str, str]:
    """Validate required API keys and return them."""
    keys = {}

    if dry_run:
        return keys

    if "tavily" in sources:
        tavily_key = os.environ.get("TAVILY_API_KEY", "")
        if not tavily_key:
            print("ERROR: TAVILY_API_KEY environment variable not set")
            sys.exit(1)
        keys["tavily"] = tavily_key

    # Together API is always needed for scoring (unless dry-run)
    together_key = os.environ.get("TOGETHER_API_KEY", "")
    if not together_key:
        print("ERROR: TOGETHER_API_KEY environment variable not set")
        sys.exit(1)
    keys["together"] = together_key

    return keys


def deduplicate_items(items: list[dict]) -> list[dict]:
    """Remove duplicate items by URL."""
    seen_urls = set()
    unique = []
    for item in items:
        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(item)
    return unique


def main():
    parser = argparse.ArgumentParser(
        description="Scout Agent: Daily discovery for AI agent engineering research"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making API calls (uses mock data)",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default="tavily,arxiv,youtube,github",
        help="Comma-separated list of sources to fetch (default: all)",
    )
    args = parser.parse_args()

    sources = [s.strip().lower() for s in args.sources.split(",")]
    valid_sources = {"tavily", "arxiv", "youtube", "github"}
    invalid = set(sources) - valid_sources
    if invalid:
        print(f"ERROR: Invalid sources: {invalid}")
        print(f"Valid sources: {valid_sources}")
        sys.exit(1)

    print(f"Scout Agent starting...")
    print(f"  Dry-run: {args.dry_run}")
    print(f"  Sources: {sources}")
    print()

    # Validate API keys
    api_keys = validate_api_keys(sources, args.dry_run)

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    research_dir = project_root / "src" / "data" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    output_file = research_dir / f"{today}.json"

    # Fetch from sources
    all_items = []

    print("Fetching from sources...")

    if "tavily" in sources:
        print("  Tavily...")
        tavily_items = fetch_tavily(api_keys.get("tavily", ""), args.dry_run)
        print(f"    Found {len(tavily_items)} items")
        all_items.extend(tavily_items)

    if "arxiv" in sources:
        print("  arXiv...")
        arxiv_items = fetch_arxiv(args.dry_run)
        print(f"    Found {len(arxiv_items)} items")
        all_items.extend(arxiv_items)

    if "youtube" in sources:
        print("  YouTube...")
        youtube_items = fetch_youtube(args.dry_run)
        print(f"    Found {len(youtube_items)} items")
        all_items.extend(youtube_items)

    if "github" in sources:
        print("  GitHub...")
        github_items = fetch_github_trending(args.dry_run)
        print(f"    Found {len(github_items)} items")
        all_items.extend(github_items)

    print(f"\nTotal items fetched: {len(all_items)}")

    if not all_items:
        print("No items fetched, exiting.")
        return

    # Deduplicate
    all_items = deduplicate_items(all_items)
    print(f"After deduplication: {len(all_items)}")

    # Estimate tokens and cost
    estimated_tokens = estimate_tokens(all_items)
    estimated_cost = estimate_cost(estimated_tokens)
    print(f"Estimated tokens for scoring: {estimated_tokens}")
    print(f"Estimated cost: ${estimated_cost:.4f}")

    # Score with Together API
    print("\nScoring items with Together API...")
    scored_items = score_items_with_together(
        all_items, api_keys.get("together", ""), args.dry_run
    )

    # Filter to relevant items (score >= 0.5)
    relevant_items = [item for item in scored_items if item.get("relevance_score", 0) >= 0.5]
    print(f"Relevant items (score >= 0.5): {len(relevant_items)}")

    # Sort by relevance score
    relevant_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    # Prepare output
    output = {
        "date": today,
        "stats": {
            "sources_checked": len(sources),
            "items_found": len(all_items),
            "items_relevant": len(relevant_items),
            "tokens_used": estimated_tokens,
            "cost_usd": round(estimated_cost, 4),
        },
        "findings": relevant_items,
    }

    # Save output
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nOutput saved to: {output_file}")
    print(f"Stats: {json.dumps(output['stats'], indent=2)}")


if __name__ == "__main__":
    main()
