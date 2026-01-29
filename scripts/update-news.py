#!/usr/bin/env python3
"""
Fetch news from AI/agent-related sources and use Claude to process them.
Updates src/data/news.json which is read by the Resources page.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import anthropic
import feedparser
import httpx

# RSS feeds to monitor
# Note: All URLs verified working as of Jan 2026
FEEDS = [
    {
        "name": "LangChain Blog",
        "url": "https://blog.langchain.dev/rss",
        "category": "frameworks",
    },
    {
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
        "category": "providers",
    },
    {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "category": "providers",
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "tools",
    },
    {
        "name": "LlamaIndex Blog",
        "url": "https://medium.com/feed/llamaindex-blog",
        "category": "frameworks",
    },
]

# How many days back to look for news
LOOKBACK_DAYS = 7

# Maximum news items to keep
MAX_NEWS_ITEMS = 20


def fetch_feed(feed_config: dict) -> list[dict]:
    """Fetch and parse an RSS feed."""
    try:
        response = httpx.get(
            feed_config["url"],
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "AgentEngineering-NewsBot/1.0"}
        )
        response.raise_for_status()
        parsed = feedparser.parse(response.text)

        if parsed.bozo and not parsed.entries:
            print(f"  Warning: Feed {feed_config['name']} returned invalid XML")
            return []

        cutoff = datetime.now() - timedelta(days=LOOKBACK_DAYS)
        items = []

        for entry in parsed.entries[:10]:  # Limit per feed
            # Parse publish date
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])

            if published and published < cutoff:
                continue

            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "summary": entry.get("summary", "")[:500],  # Truncate
                "published": published.isoformat() if published else None,
                "source": feed_config["name"],
                "category": feed_config["category"],
            })

        return items
    except httpx.HTTPStatusError as e:
        print(f"  Error fetching {feed_config['name']}: HTTP {e.response.status_code}")
        return []
    except httpx.RequestError as e:
        print(f"  Error fetching {feed_config['name']}: {type(e).__name__} - {e}")
        return []
    except Exception as e:
        print(f"  Error fetching {feed_config['name']}: {type(e).__name__} - {e}")
        return []


def fetch_all_news() -> list[dict]:
    """Fetch news from all configured feeds."""
    all_items = []
    for feed in FEEDS:
        print(f"Fetching {feed['name']}...")
        items = fetch_feed(feed)
        all_items.extend(items)
        print(f"  Found {len(items)} items")
    return all_items


def filter_and_summarize_with_claude(items: list[dict]) -> list[dict]:
    """Use Claude to filter relevant news and generate summaries."""
    if not items:
        return []

    client = anthropic.Anthropic()

    # Prepare items for Claude
    items_text = "\n\n".join([
        f"[{i}] {item['title']}\nSource: {item['source']}\nURL: {item['url']}\nSummary: {item['summary']}"
        for i, item in enumerate(items)
    ])

    prompt = f"""You are an AI agent engineering news curator. Review these news items and select the ones most relevant to AI agent development, including:
- Agent frameworks and libraries (LangChain, LangGraph, AutoGen, CrewAI, etc.)
- LLM providers and models (Claude, GPT, Gemini, open source models)
- Agent protocols (MCP, A2A)
- Agent patterns (ReAct, tool use, memory, multi-agent)
- RAG and retrieval systems
- Agent evaluation and benchmarks
- Agent safety and guardrails

For each relevant item, provide:
1. The item number [N]
2. A concise 1-2 sentence summary focused on what's relevant to agent engineering
3. Tags (2-4 relevant tags from: frameworks, models, protocols, patterns, rag, evaluation, safety, tools, research)

Skip items that are:
- General AI/ML news not specific to agents
- Product announcements without technical substance
- Duplicate or very similar to other items

NEWS ITEMS:
{items_text}

Respond in JSON format:
{{
  "selected": [
    {{
      "index": 0,
      "summary": "...",
      "tags": ["tag1", "tag2"]
    }}
  ]
}}

Select the top 5-10 most relevant items."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        # Extract JSON from response
        response_text = response.content[0].text
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text)

        processed = []
        for selected in result.get("selected", []):
            idx = selected["index"]
            if 0 <= idx < len(items):
                item = items[idx].copy()
                item["summary"] = selected["summary"]
                item["tags"] = selected["tags"]
                item["processed_at"] = datetime.now().isoformat()
                processed.append(item)

        return processed
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error parsing Claude response: {e}")
        return []


def load_existing_news(path: Path) -> list[dict]:
    """Load existing news items."""
    if path.exists():
        with open(path) as f:
            data = json.load(f)
            return data.get("items", [])
    return []


def merge_news(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge new items with existing, avoiding duplicates."""
    existing_urls = {item["url"] for item in existing}

    merged = list(existing)
    for item in new:
        if item["url"] not in existing_urls:
            merged.insert(0, item)  # New items at the top
            existing_urls.add(item["url"])

    # Sort by date and limit
    merged.sort(
        key=lambda x: x.get("published") or x.get("processed_at") or "",
        reverse=True
    )
    return merged[:MAX_NEWS_ITEMS]


def main():
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set the ANTHROPIC_API_KEY secret in your GitHub repository settings")
        raise SystemExit(1)

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "src" / "data"
    news_file = data_dir / "news.json"

    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Fetch news
    print("Fetching news from feeds...")
    raw_items = fetch_all_news()
    print(f"Total items fetched: {len(raw_items)}")

    if not raw_items:
        print("WARNING: No items fetched from any feed.")
        print("This could indicate network issues or changed feed URLs.")
        # Don't fail - just skip processing
        return

    # Process with Claude
    print("\nProcessing with Claude...")
    try:
        processed_items = filter_and_summarize_with_claude(raw_items)
        print(f"Relevant items after processing: {len(processed_items)}")
    except anthropic.APIError as e:
        print(f"ERROR: Anthropic API error: {e}")
        raise SystemExit(1)

    if not processed_items:
        print("No relevant items after filtering, exiting.")
        return

    # Merge with existing
    existing_items = load_existing_news(news_file)
    merged_items = merge_news(existing_items, processed_items)

    # Save
    output = {
        "last_updated": datetime.now().isoformat(),
        "items": merged_items,
    }

    with open(news_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(merged_items)} items to {news_file}")
    print(f"New items added: {len(merged_items) - len(existing_items)}")


if __name__ == "__main__":
    main()
