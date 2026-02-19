#!/usr/bin/env python3
"""
Fetch news from AI/agent-related sources and use Claude to process them.
Updates src/data/news.json which is read by the Resources page.

Sources:
  - RSS feeds from major AI/agent blogs
  - Twitter/X accounts of key researchers and practitioners
"""

import json
import os
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

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

# Twitter/X accounts to monitor for article links
TWITTER_ACCOUNTS = [
    "RLanceMartin",
    "bromann",
    "UnslothAI",
    "Vtrivedy10",
    "hwchase17",
    "LangChain",
    "amorriscode",
    "karpathy",
    "bcherny",
    "trq212",
    "LangChain_JS",
    "Letta_AI",
]

# Domains to skip when extracting article URLs from tweets
TWITTER_SKIP_DOMAINS = {"twitter.com", "x.com", "t.co", "pic.twitter.com"}

TWITTER_API_BASE = "https://api.twitter.com/2"

# How many days back to look for news
LOOKBACK_DAYS = 7

# Maximum news items to keep
MAX_NEWS_ITEMS = 20


# ---------------------------------------------------------------------------
# RSS feed fetching
# ---------------------------------------------------------------------------

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


def fetch_all_feeds() -> list[dict]:
    """Fetch news from all configured RSS feeds."""
    all_items = []
    for feed in FEEDS:
        print(f"Fetching {feed['name']}...")
        items = fetch_feed(feed)
        all_items.extend(items)
        print(f"  Found {len(items)} items")
    return all_items


# ---------------------------------------------------------------------------
# Twitter/X fetching
# ---------------------------------------------------------------------------

def twitter_headers() -> dict | None:
    """Return auth headers for X API, or None if no token configured."""
    token = os.environ.get("TWITTER_BEARER_TOKEN")
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "AgentEngineering-NewsBot/1.0",
    }


def fetch_twitter_user_ids(handles: list[str], headers: dict) -> dict[str, str]:
    """Batch-resolve Twitter handles to user IDs."""
    try:
        resp = httpx.get(
            f"{TWITTER_API_BASE}/users/by",
            params={"usernames": ",".join(handles)},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {u["username"].lower(): u["id"] for u in data.get("data", [])}
    except Exception as e:
        print(f"  Error fetching Twitter user IDs: {e}")
        return {}


def fetch_user_tweets(user_id: str, headers: dict) -> list[dict]:
    """Fetch tweets from the last LOOKBACK_DAYS days for a user."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    try:
        resp = httpx.get(
            f"{TWITTER_API_BASE}/users/{user_id}/tweets",
            params={
                "max_results": 10,
                "tweet.fields": "entities,created_at",
                "start_time": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "exclude": "retweets,replies",
            },
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception as e:
        print(f"  Error fetching tweets for user {user_id}: {e}")
        return []


def extract_article_urls(tweets: list[dict]) -> list[str]:
    """Pull external article URLs out of tweet entities, deduped."""
    seen: set[str] = set()
    urls: list[str] = []
    for tweet in tweets:
        for url_entity in tweet.get("entities", {}).get("urls", []):
            expanded = url_entity.get("expanded_url", "")
            if not expanded or expanded in seen:
                continue
            domain = urlparse(expanded).netloc.lstrip("www.")
            if any(skip in domain for skip in TWITTER_SKIP_DOMAINS):
                continue
            seen.add(expanded)
            urls.append(expanded)
    return urls


class _TextExtractor(HTMLParser):
    """Minimal HTML-to-text converter using stdlib only."""

    _SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            stripped = data.strip()
            if stripped:
                self._parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._parts)


def fetch_article_content(url: str) -> str | None:
    """Fetch a URL and return extracted plain text (max 3 000 chars)."""
    try:
        resp = httpx.get(
            url,
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "AgentEngineering-NewsBot/1.0"},
        )
        resp.raise_for_status()
        extractor = _TextExtractor()
        extractor.feed(resp.text)
        text = extractor.get_text()
        return text[:3000] if text else None
    except Exception as e:
        print(f"    Could not fetch article {url}: {e}")
        return None


def fetch_twitter_news(headers: dict) -> list[dict]:
    """Fetch article links from all monitored Twitter accounts."""
    print("Looking up Twitter user IDs...")
    user_ids = fetch_twitter_user_ids(TWITTER_ACCOUNTS, headers)
    if not user_ids:
        print("  No user IDs resolved — check token or account list.")
        return []

    all_items: list[dict] = []

    for handle in TWITTER_ACCOUNTS:
        uid = user_ids.get(handle.lower())
        if not uid:
            print(f"  @{handle}: user ID not found, skipping")
            continue

        tweets = fetch_user_tweets(uid, headers)
        article_urls = extract_article_urls(tweets)

        if not article_urls:
            print(f"  @{handle}: no article links in recent tweets")
            continue

        print(f"  @{handle}: {len(article_urls)} article(s) found")
        for url in article_urls:
            print(f"    Fetching: {url}")
            content = fetch_article_content(url)
            if content:
                all_items.append({
                    # Title placeholder — Claude will extract the real one
                    "title": f"[Article shared by @{handle}]",
                    "url": url,
                    "summary": content,
                    "published": datetime.now(timezone.utc).isoformat(),
                    "source": f"@{handle} on X",
                    "category": "community",
                    "_needs_title": True,  # Signal to Claude
                })

    return all_items


# ---------------------------------------------------------------------------
# Claude filtering & summarisation
# ---------------------------------------------------------------------------

def filter_and_summarize_with_claude(items: list[dict]) -> list[dict]:
    """Use Claude to filter relevant news and generate summaries."""
    if not items:
        return []

    client = anthropic.Anthropic()

    items_text = "\n\n".join([
        f"[{i}] {item['title']}\nSource: {item['source']}\nURL: {item['url']}\n"
        f"{'Article content' if item.get('_needs_title') else 'Summary'}: {item['summary']}"
        for i, item in enumerate(items)
    ])

    prompt = f"""You are an AI agent engineering news curator. Review these items and select the ones most relevant to AI agent development, including:
- Agent frameworks and libraries (LangChain, LangGraph, AutoGen, CrewAI, etc.)
- LLM providers and models (Claude, GPT, Gemini, open source models)
- Agent protocols (MCP, A2A)
- Agent patterns (ReAct, tool use, memory, multi-agent)
- RAG and retrieval systems
- Agent evaluation and benchmarks
- Agent safety and guardrails

For each relevant item, provide:
1. The item number [N]
2. A title — for items whose title starts with "[Article shared by", extract a proper title from the article content; otherwise use the existing title
3. A concise 1-2 sentence summary focused on what's relevant to agent engineering
4. Tags (2-4 relevant tags from: frameworks, models, protocols, patterns, rag, evaluation, safety, tools, research)

## Summarisation standards

- **Stick to what the source says.** Do not add interpretation, context, or implications not stated in the original.
- **No hype or promotional language.** Strip marketing tone. Avoid "revolutionary", "groundbreaking", "game-changing" unless the source provides concrete evidence.
- **Use measured language.** Prefer "may improve", "is reported to", "according to", "aims to".
- **If the item is thin, skip it.** A vague announcement without technical substance is not worth including.
- **Do not infer impact.** Describe what the thing is and does, not what it might mean.

Skip items that are:
- General AI/ML news not specific to agents
- Product announcements without technical substance
- Duplicate or very similar to other items
- Too vague or speculative to summarise accurately

NEWS ITEMS:
{items_text}

Respond in JSON format:
{{
  "selected": [
    {{
      "index": 0,
      "title": "Proper article title here",
      "summary": "...",
      "tags": ["tag1", "tag2"]
    }}
  ]
}}

Select the top 5-10 most relevant items. Fewer high-quality items is better than padding with weak ones."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        response_text = response.content[0].text
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
                item.pop("_needs_title", None)
                item["title"] = selected.get("title") or item["title"]
                item["summary"] = selected["summary"]
                item["tags"] = selected["tags"]
                item["processed_at"] = datetime.now().isoformat()
                processed.append(item)

        return processed
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error parsing Claude response: {e}")
        return []


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def load_existing_news(path: Path) -> list[dict]:
    if path.exists():
        with open(path) as f:
            return json.load(f).get("items", [])
    return []


def merge_news(existing: list[dict], new: list[dict]) -> list[dict]:
    existing_urls = {item["url"] for item in existing}
    merged = list(existing)
    for item in new:
        if item["url"] not in existing_urls:
            merged.insert(0, item)
            existing_urls.add(item["url"])
    merged.sort(
        key=lambda x: x.get("published") or x.get("processed_at") or "",
        reverse=True,
    )
    return merged[:MAX_NEWS_ITEMS]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        raise SystemExit(1)

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "src" / "data"
    news_file = data_dir / "news.json"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Collect from RSS feeds
    print("Fetching RSS feeds...")
    raw_items = fetch_all_feeds()
    print(f"Total RSS items: {len(raw_items)}")

    # Collect from Twitter/X
    headers = twitter_headers()
    if headers:
        print("\nFetching Twitter/X articles...")
        twitter_items = fetch_twitter_news(headers)
        print(f"Twitter articles found: {len(twitter_items)}")
        raw_items.extend(twitter_items)
    else:
        print("\nSkipping Twitter/X (TWITTER_BEARER_TOKEN not set)")

    if not raw_items:
        print("WARNING: No items fetched from any source.")
        return

    print(f"\nTotal items to process: {len(raw_items)}")

    # Filter and summarise with Claude
    print("\nProcessing with Claude...")
    try:
        processed_items = filter_and_summarize_with_claude(raw_items)
        print(f"Relevant items after filtering: {len(processed_items)}")
    except anthropic.APIError as e:
        print(f"ERROR: Anthropic API error: {e}")
        raise SystemExit(1)

    if not processed_items:
        print("No relevant items after filtering, exiting.")
        return

    existing_items = load_existing_news(news_file)
    merged_items = merge_news(existing_items, processed_items)

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
