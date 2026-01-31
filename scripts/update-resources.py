#!/usr/bin/env python3
"""
Update Resources: Extract valuable resources from deep dive analyses.

Parses deep dive results and extracts papers, repos, tools, and articles
that are highly relevant to add to the auto-discovered resources list.

Usage:
    python scripts/update-resources.py [options]

Options:
    --dry-run           Show what would be added without saving
    --weeks N           Number of weeks of deep dives to process (default: 4)
    --min-score N       Minimum bulk_score to include (default: 7)

Examples:
    python scripts/update-resources.py --dry-run
    python scripts/update-resources.py --weeks 2 --min-score 8
"""

import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# =============================================================================
# Configuration
# =============================================================================

# Category mapping based on source and type
CATEGORY_MAP = {
    "paper": "papers",
    "repo": "repos",
    "video": "tutorials",
    "article": "articles",
}

# Topic to category hints
TOPIC_CATEGORY_HINTS = {
    "tool-use": "papers",
    "react-pattern": "papers",
    "memory": "papers",
    "multi-agent": "papers",
    "mcp": "tools",
    "orchestration": "frameworks",
    "rag": "papers",
    "evaluation": "tools",
    "guardrails": "tools",
    "planning": "papers",
}

# Maximum resources per category
MAX_PER_CATEGORY = 20

# =============================================================================
# Resource Extraction
# =============================================================================


def extract_resource_from_item(item: dict) -> Optional[dict]:
    """Extract a resource entry from a deep dive item."""
    tier1 = item.get("tier1_analysis", {})
    deep_dive = item.get("deep_dive", {})

    # Skip low-scoring items
    bulk_score = tier1.get("bulk_score", 0)
    if bulk_score < 7:
        return None

    item_type = item.get("type", "article")
    source = item.get("source", "unknown")
    url = item.get("url", "")
    title = item.get("title", "")

    if not url or not title:
        return None

    # Determine category
    category = CATEGORY_MAP.get(item_type, "articles")

    # Override category based on topics if deep dive suggests tools/frameworks
    topics = tier1.get("topics", [])
    if deep_dive:
        site_relevance = deep_dive.get("site_relevance", {})
        topics = site_relevance.get("topics", topics)

    # Build description
    description = tier1.get("summary", "")
    if deep_dive and deep_dive.get("key_contribution"):
        description = deep_dive["key_contribution"]

    # Extract additional metadata based on type
    metadata = {}

    if item_type == "paper":
        # Try to extract author/year from title or metadata
        raw = item.get("raw_metadata", {})
        if "arxiv_id" in raw:
            metadata["arxiv_id"] = raw["arxiv_id"]
        # arXiv IDs often contain year: 2601.12345 -> 2026
        arxiv_match = re.search(r"/(\d{4})\.(\d+)", url)
        if arxiv_match:
            year_prefix = arxiv_match.group(1)[:2]
            metadata["year"] = 2000 + int(year_prefix) if int(year_prefix) < 50 else 1900 + int(year_prefix)

    elif item_type == "repo":
        raw = item.get("raw_metadata", {})
        if "stars" in raw:
            metadata["stars"] = raw["stars"]
        if "language" in raw:
            metadata["language"] = raw["language"]

    elif item_type == "video":
        raw = item.get("raw_metadata", {})
        if "channel" in raw:
            metadata["channel"] = raw["channel"]

    # Build resource entry
    resource = {
        "title": title,
        "url": url,
        "description": description[:300] if description else "",
        "category": category,
        "source": source,
        "type": item_type,
        "topics": topics[:5],  # Limit topics
        "score": bulk_score,
        "discovered_at": datetime.now().isoformat(),
        "metadata": metadata,
    }

    return resource


def load_deep_dives(deep_dives_dir: Path, weeks: int) -> list[dict]:
    """Load recent deep dive results."""
    all_items = []

    # Get list of deep dive files
    if not deep_dives_dir.exists():
        return []

    files = sorted(deep_dives_dir.glob("*.json"), reverse=True)

    # Process up to N weeks
    for file_path in files[:weeks]:
        try:
            with open(file_path) as f:
                data = json.load(f)
                analyses = data.get("analyses", [])
                all_items.extend(analyses)
                print(f"  Loaded {len(analyses)} items from {file_path.name}")
        except Exception as e:
            print(f"  Warning: Failed to load {file_path.name}: {e}")

    return all_items


def load_existing_resources(resources_file: Path) -> dict:
    """Load existing resources data."""
    if resources_file.exists():
        try:
            with open(resources_file) as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "last_updated": None,
        "papers": [],
        "repos": [],
        "tutorials": [],
        "articles": [],
    }


def get_existing_urls(resources: dict) -> set[str]:
    """Get all URLs from existing resources."""
    urls = set()
    for category in ["papers", "repos", "tutorials", "articles"]:
        for item in resources.get(category, []):
            urls.add(item.get("url", ""))
    return urls


def categorize_and_dedupe(
    new_resources: list[dict], existing_resources: dict, min_score: int
) -> dict:
    """Categorize new resources and deduplicate against existing."""
    existing_urls = get_existing_urls(existing_resources)

    # Also check hardcoded resources URLs (from the astro page)
    # These are the foundational papers that shouldn't be duplicated
    hardcoded_urls = {
        "https://arxiv.org/abs/2210.03629",  # ReAct
        "https://arxiv.org/abs/2302.04761",  # Toolformer
        "https://arxiv.org/abs/2201.11903",  # Chain-of-Thought
        "https://arxiv.org/abs/2305.10601",  # Tree of Thoughts
        "https://arxiv.org/abs/2304.03442",  # Generative Agents
        "https://arxiv.org/abs/2310.08560",  # MemGPT
        "https://arxiv.org/abs/2303.11366",  # Reflexion
        "https://arxiv.org/abs/2308.08155",  # AutoGen
        "https://arxiv.org/abs/2308.00352",  # MetaGPT
        "https://arxiv.org/abs/2305.19118",  # Multi-Agent Debate
        "https://arxiv.org/abs/2005.11401",  # RAG
        "https://arxiv.org/abs/2310.11511",  # Self-RAG
        "https://arxiv.org/abs/2401.15884",  # CRAG
        "https://arxiv.org/abs/2404.16130",  # Graph RAG
        "https://arxiv.org/abs/2310.06770",  # SWE-bench
        "https://arxiv.org/abs/2307.13854",  # WebArena
        "https://arxiv.org/abs/2311.12983",  # GAIA
        "https://arxiv.org/abs/2308.03688",  # AgentBench
        "https://arxiv.org/abs/2212.08073",  # Constitutional AI
        "https://arxiv.org/abs/2202.03286",  # Red Teaming
    }
    existing_urls.update(hardcoded_urls)

    # Categorize new resources
    categorized = {
        "papers": list(existing_resources.get("papers", [])),
        "repos": list(existing_resources.get("repos", [])),
        "tutorials": list(existing_resources.get("tutorials", [])),
        "articles": list(existing_resources.get("articles", [])),
    }

    added_count = 0
    skipped_duplicate = 0
    skipped_low_score = 0

    for resource in new_resources:
        url = resource.get("url", "")
        score = resource.get("score", 0)
        category = resource.get("category", "articles")

        # Skip if already exists
        if url in existing_urls:
            skipped_duplicate += 1
            continue

        # Skip if below minimum score
        if score < min_score:
            skipped_low_score += 1
            continue

        # Add to appropriate category
        if category in categorized:
            categorized[category].append(resource)
            existing_urls.add(url)
            added_count += 1

    # Sort each category by score and limit
    for category in categorized:
        categorized[category] = sorted(
            categorized[category],
            key=lambda x: x.get("score", 0),
            reverse=True,
        )[:MAX_PER_CATEGORY]

    print(f"  Added: {added_count}")
    print(f"  Skipped (duplicate): {skipped_duplicate}")
    print(f"  Skipped (low score): {skipped_low_score}")

    return categorized


# =============================================================================
# Main Logic
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Update Resources: Extract resources from deep dive analyses"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be added without saving",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=4,
        help="Number of weeks of deep dives to process (default: 4)",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=7,
        help="Minimum bulk_score to include (default: 7)",
    )
    args = parser.parse_args()

    print("Update Resources starting...")
    print(f"  Dry-run: {args.dry_run}")
    print(f"  Weeks: {args.weeks}")
    print(f"  Min score: {args.min_score}")
    print()

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    deep_dives_dir = project_root / "src" / "data" / "deep-dives"
    resources_file = project_root / "src" / "data" / "resources.json"

    # Load deep dive results
    print("Loading deep dive results...")
    items = load_deep_dives(deep_dives_dir, args.weeks)
    print(f"Total items loaded: {len(items)}")

    if not items:
        print("No deep dive results found.")
        return

    # Extract resources from items
    print("\nExtracting resources...")
    new_resources = []
    for item in items:
        resource = extract_resource_from_item(item)
        if resource:
            new_resources.append(resource)

    print(f"Extracted {len(new_resources)} potential resources")

    # Load existing resources
    print("\nLoading existing resources...")
    existing_resources = load_existing_resources(resources_file)

    # Categorize and dedupe
    print("\nCategorizing and deduplicating...")
    updated_resources = categorize_and_dedupe(
        new_resources, existing_resources, args.min_score
    )

    # Add metadata
    output = {
        "last_updated": datetime.now().isoformat(),
        **updated_resources,
    }

    # Summary
    print("\nResource counts:")
    for category in ["papers", "repos", "tutorials", "articles"]:
        count = len(output.get(category, []))
        print(f"  {category}: {count}")

    if args.dry_run:
        print("\n[DRY-RUN] Would save to:", resources_file)
        print("\nNew resources preview:")
        for category in ["papers", "repos", "tutorials", "articles"]:
            items = output.get(category, [])
            new_items = [i for i in items if i.get("discovered_at", "").startswith(datetime.now().strftime("%Y-%m-%d"))]
            if new_items:
                print(f"\n  {category.upper()}:")
                for item in new_items[:3]:
                    print(f"    - {item['title'][:60]}... (score: {item.get('score', 'N/A')})")
    else:
        # Save
        with open(resources_file, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nSaved to: {resources_file}")


if __name__ == "__main__":
    main()
