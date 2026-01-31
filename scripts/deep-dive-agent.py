#!/usr/bin/env python3
"""
Deep Dive Agent: Weekly deep analysis of top research discoveries.

Processes the week's scout findings using a tiered LLM approach:
- Tier 1: Together API (GPT-OSS 120B) for bulk processing all items
- Tier 2: Claude for premium analysis of top-ranked items

Usage:
    python scripts/deep-dive-agent.py [options]

Options:
    --dry-run           Run without API calls (uses mock data)
    --tier1-only        Only run Tier 1 bulk processing
    --limit N           Limit number of items to process
    --week YYYY-WW      Process specific week (default: current)

Examples:
    python scripts/deep-dive-agent.py --dry-run
    python scripts/deep-dive-agent.py --tier1-only --limit 5
    python scripts/deep-dive-agent.py --week 2026-W05
"""

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import anthropic
import httpx

# =============================================================================
# Configuration
# =============================================================================

TOGETHER_MODEL = "togethercomputer/gpt-oss-120b"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Tier 1 threshold: items with bulk_score >= this go to Tier 2
TIER2_THRESHOLD = 7

# Maximum items for Tier 2 deep analysis
MAX_TIER2_ITEMS = 10

# Site topics for relevance mapping
SITE_TOPICS = [
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
# Content Extraction
# =============================================================================


def extract_arxiv_pdf_text(arxiv_url: str, dry_run: bool = False) -> str:
    """Download arXiv PDF and extract text."""
    if dry_run:
        return "[DRY-RUN] This would be the extracted text from the arXiv PDF."

    try:
        # Convert abstract URL to PDF URL
        # https://arxiv.org/abs/2601.12345 -> https://arxiv.org/pdf/2601.12345.pdf
        arxiv_id = arxiv_url.split("/abs/")[-1]
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        # Download PDF to temp file
        response = httpx.get(
            pdf_url,
            timeout=60,
            follow_redirects=True,
            headers={"User-Agent": "AgentEngineering-DeepDive/1.0"},
        )
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(response.content)
            temp_path = f.name

        try:
            # Extract text using pypdf
            from pypdf import PdfReader

            reader = PdfReader(temp_path)
            text_parts = []
            for page in reader.pages[:20]:  # Limit to first 20 pages
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)
            # Truncate to ~15K chars to manage token costs
            return full_text[:15000]
        finally:
            Path(temp_path).unlink(missing_ok=True)

    except Exception as e:
        print(f"    Warning: PDF extraction failed: {e}")
        return ""


def extract_youtube_transcript(video_url: str, dry_run: bool = False) -> str:
    """Extract transcript from YouTube video."""
    if dry_run:
        return "[DRY-RUN] This would be the YouTube video transcript."

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # Extract video ID from URL
        # https://youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID
        if "watch?v=" in video_url:
            video_id = video_url.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]
        else:
            return ""

        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([segment["text"] for segment in transcript])
        # Truncate to ~15K chars
        return full_text[:15000]

    except Exception as e:
        print(f"    Warning: Transcript extraction failed: {e}")
        return ""


def extract_article_content(url: str, tavily_key: str, dry_run: bool = False) -> str:
    """Extract article content using Tavily."""
    if dry_run:
        return "[DRY-RUN] This would be the extracted article content."

    if not tavily_key:
        return ""

    try:
        response = httpx.post(
            "https://api.tavily.com/extract",
            json={
                "api_key": tavily_key,
                "urls": [url],
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if results:
            content = results[0].get("raw_content", "")
            # Truncate to ~15K chars
            return content[:15000]
        return ""

    except Exception as e:
        print(f"    Warning: Article extraction failed: {e}")
        return ""


def extract_content(item: dict, tavily_key: str, dry_run: bool = False) -> str:
    """Extract full content based on item type."""
    item_type = item.get("type", "")
    url = item.get("url", "")

    if item_type == "paper":
        return extract_arxiv_pdf_text(url, dry_run)
    elif item_type == "video":
        return extract_youtube_transcript(url, dry_run)
    elif item_type in ("article", "repo"):
        # For repos, we could fetch README, but for now just use the summary
        if item_type == "repo":
            return item.get("summary", "")
        return extract_article_content(url, tavily_key, dry_run)
    else:
        return item.get("summary", "")


# =============================================================================
# Tier 1: Bulk Processing with Together API
# =============================================================================


def tier1_bulk_analyze(items: list[dict], api_key: str, dry_run: bool = False) -> list[dict]:
    """Tier 1: Analyze all items with Together API for initial scoring."""
    if not items:
        return []

    if dry_run:
        print(f"  [DRY-RUN] Would bulk analyze {len(items)} items with Together API")
        results = []
        for item in items:
            result = item.copy()
            result["tier1_analysis"] = {
                "summary": "[DRY-RUN] Bulk analysis summary",
                "key_ideas": ["idea1", "idea2"],
                "bulk_score": 8,
                "topics": ["tool-use", "memory"],
                "has_code": False,
                "novelty": "medium",
                "recommend_deep_dive": True,
            }
            results.append(result)
        return results

    # Process in batches to avoid token limits
    batch_size = 10
    all_results = []

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        print(f"  Processing batch {i // batch_size + 1}/{(len(items) + batch_size - 1) // batch_size}...")

        items_text = "\n\n".join([
            f"[{j}] {item['title']}\n"
            f"Type: {item['type']}\n"
            f"Source: {item['source']}\n"
            f"Summary: {item.get('summary', 'N/A')[:500]}"
            for j, item in enumerate(batch)
        ])

        prompt = f"""Analyze these research items about AI agents. For each item, provide:

1. summary: 2-3 sentence summary of the content
2. key_ideas: List of 2-4 key ideas or contributions
3. bulk_score: Relevance score 1-10 for AI agent engineering
4. topics: Relevant topics from [{', '.join(SITE_TOPICS)}]
5. has_code: Whether the item contains code examples
6. novelty: "high", "medium", or "low"
7. recommend_deep_dive: true if worth deeper analysis

ITEMS:
{items_text}

Respond in JSON format only:
{{
  "analyses": [
    {{
      "index": 0,
      "summary": "...",
      "key_ideas": ["...", "..."],
      "bulk_score": 8,
      "topics": ["tool-use"],
      "has_code": false,
      "novelty": "medium",
      "recommend_deep_dive": true
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

            response_text = data["choices"][0]["message"]["content"]

            # Handle markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            result = json.loads(response_text.strip())

            # Apply analyses to items
            scored_indices = set()
            for analysis in result.get("analyses", []):
                idx = analysis.get("index", -1)
                if 0 <= idx < len(batch):
                    scored_indices.add(idx)
                    item_result = batch[idx].copy()
                    item_result["tier1_analysis"] = {
                        "summary": analysis.get("summary", ""),
                        "key_ideas": analysis.get("key_ideas", []),
                        "bulk_score": analysis.get("bulk_score", 0),
                        "topics": analysis.get("topics", []),
                        "has_code": analysis.get("has_code", False),
                        "novelty": analysis.get("novelty", "low"),
                        "recommend_deep_dive": analysis.get("recommend_deep_dive", False),
                    }
                    all_results.append(item_result)

            # Add any items that weren't scored with default analysis
            for idx, item in enumerate(batch):
                if idx not in scored_indices:
                    item_result = item.copy()
                    item_result["tier1_analysis"] = {
                        "summary": item.get("summary", "")[:200],
                        "key_ideas": [],
                        "bulk_score": 5,
                        "topics": item.get("topics", []),
                        "has_code": False,
                        "novelty": "low",
                        "recommend_deep_dive": False,
                    }
                    all_results.append(item_result)

        except Exception as e:
            print(f"    Warning: Tier 1 batch failed: {e}")
            # Add items with default analysis
            for item in batch:
                result = item.copy()
                result["tier1_analysis"] = {
                    "summary": item.get("summary", "")[:200],
                    "key_ideas": [],
                    "bulk_score": 5,
                    "topics": item.get("topics", []),
                    "has_code": False,
                    "novelty": "low",
                    "recommend_deep_dive": False,
                }
                all_results.append(result)

    return all_results


# =============================================================================
# Tier 2: Deep Analysis with Claude
# =============================================================================


def tier2_deep_analyze(
    item: dict, content: str, client: anthropic.Anthropic, dry_run: bool = False
) -> dict:
    """Tier 2: Deep analysis of a single item with Claude."""
    if dry_run:
        return {
            "key_contribution": "[DRY-RUN] Key contribution analysis",
            "techniques": [
                {"name": "Example Technique", "description": "Description of the technique"}
            ],
            "code_snippets": [],
            "practical_applications": ["Application 1", "Application 2"],
            "site_relevance": {
                "topics": ["tool-use", "memory"],
                "suggested_updates": [
                    {
                        "page": "/topics/tool-use/",
                        "section": "Advanced Patterns",
                        "suggestion": "Add section on this technique",
                    }
                ],
            },
        }

    tier1 = item.get("tier1_analysis", {})

    prompt = f"""You are analyzing high-value content for an AI agents knowledge base.

Previous bulk analysis flagged this as highly relevant:
- Summary: {tier1.get('summary', 'N/A')}
- Key Ideas: {tier1.get('key_ideas', [])}
- Topics: {tier1.get('topics', [])}
- Novelty: {tier1.get('novelty', 'unknown')}

ITEM METADATA:
- Title: {item.get('title', 'Unknown')}
- Type: {item.get('type', 'unknown')}
- Source: {item.get('source', 'unknown')}
- URL: {item.get('url', '')}

FULL CONTENT:
{content[:12000]}

Provide a detailed analysis in JSON format:
{{
  "key_contribution": "What's genuinely new or valuable here? (2-3 sentences)",
  "techniques": [
    {{
      "name": "Technique name",
      "description": "How it works and why it matters"
    }}
  ],
  "code_snippets": [
    {{
      "language": "python",
      "description": "What this code does",
      "code": "reconstructed or extracted code"
    }}
  ],
  "practical_applications": ["How agent builders can use this"],
  "site_relevance": {{
    "topics": ["which site topics this relates to"],
    "suggested_updates": [
      {{
        "page": "/topics/TOPIC/",
        "section": "Section name",
        "suggestion": "What to add or update"
      }}
    ]
  }}
}}

Focus on actionable insights for developers building AI agents."""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text

        # Handle markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        return json.loads(response_text.strip())

    except Exception as e:
        print(f"    Warning: Tier 2 analysis failed: {e}")
        return {
            "key_contribution": "Analysis failed",
            "techniques": [],
            "code_snippets": [],
            "practical_applications": [],
            "site_relevance": {"topics": [], "suggested_updates": []},
            "error": str(e),
        }


# =============================================================================
# Data Collection
# =============================================================================


def get_week_string(date: datetime = None) -> str:
    """Get ISO week string (YYYY-WNN) for a date."""
    if date is None:
        date = datetime.now()
    year, week, _ = date.isocalendar()
    return f"{year}-W{week:02d}"


def collect_week_findings(research_dir: Path, week: str = None) -> list[dict]:
    """Collect all findings from the past week's scout results."""
    if week:
        # Parse week string to get date range
        match = re.match(r"(\d{4})-W(\d{2})", week)
        if match:
            year, week_num = int(match.group(1)), int(match.group(2))
            # Get first day of the week
            first_day = datetime.strptime(f"{year}-W{week_num}-1", "%Y-W%W-%w")
            last_day = first_day + timedelta(days=6)
        else:
            print(f"Invalid week format: {week}")
            return []
    else:
        # Current week
        today = datetime.now()
        # Go back to Monday
        first_day = today - timedelta(days=today.weekday())
        last_day = first_day + timedelta(days=6)

    print(f"Collecting findings from {first_day.date()} to {last_day.date()}")

    all_findings = []
    current = first_day

    while current <= last_day:
        date_str = current.strftime("%Y-%m-%d")
        file_path = research_dir / f"{date_str}.json"

        if file_path.exists():
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    findings = data.get("findings", [])
                    all_findings.extend(findings)
                    print(f"  Loaded {len(findings)} findings from {date_str}")
            except Exception as e:
                print(f"  Warning: Failed to load {date_str}: {e}")

        current += timedelta(days=1)

    return all_findings


def rank_for_deep_dive(items: list[dict]) -> list[dict]:
    """Rank items by priority for deep dive processing."""
    def priority_score(item: dict) -> float:
        score = item.get("relevance_score", 0) * 10  # 0-10

        # Boost for high priority
        priority = item.get("deep_dive_priority", "low")
        if priority == "high":
            score += 3
        elif priority == "medium":
            score += 1

        # Boost for papers (usually more novel)
        if item.get("type") == "paper":
            score += 1

        return score

    sorted_items = sorted(items, key=priority_score, reverse=True)
    return sorted_items


# =============================================================================
# Cost Tracking
# =============================================================================


def estimate_tier1_cost(items: list[dict]) -> float:
    """Estimate cost for Tier 1 processing."""
    # ~500 tokens per item input, ~200 tokens output
    tokens = len(items) * 700
    # GPT-OSS 120B: ~$0.50/1M tokens
    return (tokens / 1_000_000) * 0.50


def estimate_tier2_cost(items: list[dict]) -> float:
    """Estimate cost for Tier 2 processing."""
    # ~4000 tokens per item (content + prompt), ~500 tokens output
    tokens = len(items) * 4500
    # Claude Sonnet: ~$3/1M input, $15/1M output
    return (tokens / 1_000_000) * 5  # Blended rate


# =============================================================================
# Main Logic
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Deep Dive Agent: Weekly deep analysis of research discoveries"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without API calls (uses mock data)",
    )
    parser.add_argument(
        "--tier1-only",
        action="store_true",
        help="Only run Tier 1 bulk processing",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of items to process (0 = no limit)",
    )
    parser.add_argument(
        "--week",
        type=str,
        default="",
        help="Process specific week (YYYY-WNN format, default: current)",
    )
    args = parser.parse_args()

    print("Deep Dive Agent starting...")
    print(f"  Dry-run: {args.dry_run}")
    print(f"  Tier 1 only: {args.tier1_only}")
    print(f"  Limit: {args.limit or 'none'}")
    print(f"  Week: {args.week or 'current'}")
    print()

    # Validate API keys
    if not args.dry_run:
        together_key = os.environ.get("TOGETHER_API_KEY", "")
        if not together_key:
            print("ERROR: TOGETHER_API_KEY environment variable not set")
            sys.exit(1)

        if not args.tier1_only:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not anthropic_key:
                print("ERROR: ANTHROPIC_API_KEY environment variable not set")
                sys.exit(1)

        tavily_key = os.environ.get("TAVILY_API_KEY", "")
        if not tavily_key:
            print("WARNING: TAVILY_API_KEY not set - article extraction will be limited")
    else:
        together_key = ""
        tavily_key = ""

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    research_dir = project_root / "src" / "data" / "research"
    deep_dives_dir = project_root / "src" / "data" / "deep-dives"
    deep_dives_dir.mkdir(parents=True, exist_ok=True)

    week_str = args.week or get_week_string()
    output_file = deep_dives_dir / f"{week_str}.json"

    # Collect findings
    print("Collecting week's findings...")
    findings = collect_week_findings(research_dir, args.week if args.week else None)
    print(f"Total findings: {len(findings)}")

    if not findings:
        print("No findings to process.")
        # Create empty output
        output = {
            "week": week_str,
            "processed": 0,
            "stats": {
                "tier1_items": 0,
                "tier2_items": 0,
                "tier1_cost_usd": 0,
                "tier2_cost_usd": 0,
                "total_cost_usd": 0,
            },
            "analyses": [],
        }
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Empty output saved to: {output_file}")
        return

    # Deduplicate by URL
    seen_urls = set()
    unique_findings = []
    for item in findings:
        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_findings.append(item)
    findings = unique_findings
    print(f"After deduplication: {len(findings)}")

    # Rank by priority
    findings = rank_for_deep_dive(findings)

    # Apply limit
    if args.limit > 0:
        findings = findings[: args.limit]
        print(f"After limit: {len(findings)}")

    # Estimate costs
    tier1_cost = estimate_tier1_cost(findings)
    print(f"\nEstimated Tier 1 cost: ${tier1_cost:.4f}")

    # Tier 1: Bulk analysis
    print("\n=== Tier 1: Bulk Analysis ===")
    tier1_results = tier1_bulk_analyze(findings, together_key, args.dry_run)
    print(f"Tier 1 complete: {len(tier1_results)} items analyzed")

    # Filter for Tier 2
    tier2_candidates = [
        item
        for item in tier1_results
        if item.get("tier1_analysis", {}).get("bulk_score", 0) >= TIER2_THRESHOLD
        or item.get("tier1_analysis", {}).get("recommend_deep_dive", False)
    ]
    tier2_candidates = tier2_candidates[:MAX_TIER2_ITEMS]
    print(f"Tier 2 candidates (score >= {TIER2_THRESHOLD}): {len(tier2_candidates)}")

    tier2_cost = estimate_tier2_cost(tier2_candidates) if not args.tier1_only else 0
    print(f"Estimated Tier 2 cost: ${tier2_cost:.4f}")

    # Tier 2: Deep analysis
    tier2_results = []
    if not args.tier1_only and tier2_candidates:
        print("\n=== Tier 2: Deep Analysis ===")

        if not args.dry_run:
            claude_client = anthropic.Anthropic()
        else:
            claude_client = None

        for i, item in enumerate(tier2_candidates):
            print(f"  [{i + 1}/{len(tier2_candidates)}] {item.get('title', 'Unknown')[:60]}...")

            # Extract full content
            content = extract_content(item, tavily_key, args.dry_run)
            if not content:
                print("    Skipping: no content extracted")
                continue

            # Deep analysis
            deep_analysis = tier2_deep_analyze(item, content, claude_client, args.dry_run)

            result = item.copy()
            result["deep_dive"] = deep_analysis
            result["content_length"] = len(content)
            tier2_results.append(result)

        print(f"Tier 2 complete: {len(tier2_results)} items analyzed")

    # Prepare output
    analyses = []

    # Add Tier 2 results (with deep dive)
    for item in tier2_results:
        analyses.append({
            "id": item.get("id", ""),
            "type": item.get("type", ""),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "source": item.get("source", ""),
            "tier1_analysis": item.get("tier1_analysis", {}),
            "deep_dive": item.get("deep_dive", {}),
            "content_length": item.get("content_length", 0),
        })

    # Add remaining Tier 1 results (without deep dive)
    tier2_ids = {item.get("id") for item in tier2_results}
    for item in tier1_results:
        if item.get("id") not in tier2_ids:
            analyses.append({
                "id": item.get("id", ""),
                "type": item.get("type", ""),
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": item.get("source", ""),
                "tier1_analysis": item.get("tier1_analysis", {}),
            })

    # Sort by bulk score
    analyses.sort(
        key=lambda x: x.get("tier1_analysis", {}).get("bulk_score", 0),
        reverse=True,
    )

    output = {
        "week": week_str,
        "generated_at": datetime.now().isoformat(),
        "processed": len(tier1_results),
        "stats": {
            "tier1_items": len(tier1_results),
            "tier2_items": len(tier2_results),
            "tier1_cost_usd": round(tier1_cost, 4),
            "tier2_cost_usd": round(tier2_cost, 4),
            "total_cost_usd": round(tier1_cost + tier2_cost, 4),
        },
        "analyses": analyses,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nOutput saved to: {output_file}")
    print(f"Stats: {json.dumps(output['stats'], indent=2)}")


if __name__ == "__main__":
    main()
