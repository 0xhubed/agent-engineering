#!/usr/bin/env python3
"""
Content Agent: Generate PRs with suggested content updates for topic pages.

Analyzes deep dive findings and generates pull requests with copy-paste ready
content suggestions for topic page updates. Unlike other phases (which auto-commit),
this requires human review via PRs.

Usage:
    python scripts/content-agent.py [options]

Options:
    --dry-run           Preview without creating PR (default for safety)
    --weeks N           Number of weeks to process (default: 4)
    --min-confidence N  Threshold 0.0-1.0 (default: 0.7)
    --max-suggestions N Limit per PR (default: 10)

Examples:
    python scripts/content-agent.py --dry-run
    python scripts/content-agent.py --min-confidence 0.8 --max-suggestions 5
    python scripts/content-agent.py --weeks 2
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import anthropic

# =============================================================================
# Configuration
# =============================================================================

CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Default thresholds
DEFAULT_CONFIDENCE_THRESHOLD = 0.7
DEFAULT_MAX_SUGGESTIONS = 10
DEFAULT_WEEKS = 4

# Topic slug to file path mapping
TOPIC_PAGE_MAP = {
    "tool-use": "src/pages/topics/tool-use/index.astro",
    "react-pattern": "src/pages/topics/react-pattern/index.astro",
    "memory": "src/pages/topics/memory/index.astro",
    "multi-agent": "src/pages/topics/multi-agent/index.astro",
    "mcp": "src/pages/topics/mcp/index.astro",
    "orchestration": "src/pages/topics/orchestration/index.astro",
    "rag": "src/pages/topics/agentic-rag/index.astro",
    "agentic-rag": "src/pages/topics/agentic-rag/index.astro",
    "evaluation": "src/pages/topics/evaluation/index.astro",
    "guardrails": "src/pages/topics/safety/index.astro",
    "safety": "src/pages/topics/safety/index.astro",
    "planning": "src/pages/topics/planning/index.astro",
    "context-engineering": "src/pages/topics/context-engineering/index.astro",
    "context-bloat": "src/pages/topics/context-bloat/index.astro",
    "prompt-caching": "src/pages/topics/prompt-caching/index.astro",
    "skills-pattern": "src/pages/topics/skills-pattern/index.astro",
    "a2a": "src/pages/topics/a2a/index.astro",
    "mcp-apps": "src/pages/topics/mcp-apps/index.astro",
    "ucp": "src/pages/topics/ucp/index.astro",
    "learning-adaptation": "src/pages/topics/learning-adaptation/index.astro",
    "agent-fine-tuning": "src/pages/topics/agent-fine-tuning/index.astro",
}

# Source type weights for confidence scoring
SOURCE_WEIGHTS = {
    "paper": 1.0,
    "article": 0.8,
    "video": 0.7,
    "repo": 0.6,
}

# Framework standards from CLAUDE.md
FRAMEWORK_STANDARDS = """
Framework Standards for Code Samples:
- Python: Use LangChain/LangGraph (not raw OpenAI/Anthropic clients)
- C#: Use Microsoft Agent Framework (not AutoGen or Semantic Kernel directly)
- Exception: prompt-caching shows native provider APIs for provider-specific caching features
"""

# =============================================================================
# Data Loading
# =============================================================================


def get_week_string(date: datetime = None) -> str:
    """Get ISO week string (YYYY-WNN) for a date."""
    if date is None:
        date = datetime.now()
    year, week, _ = date.isocalendar()
    return f"{year}-W{week:02d}"


def load_deep_dives(deep_dives_dir: Path, weeks: int) -> list[dict]:
    """Load deep dive items with suggested_updates from recent weeks."""
    all_items = []

    if not deep_dives_dir.exists():
        return []

    files = sorted(deep_dives_dir.glob("*.json"), reverse=True)

    for file_path in files[:weeks]:
        try:
            with open(file_path) as f:
                data = json.load(f)
                week = data.get("week", file_path.stem)
                analyses = data.get("analyses", [])

                for item in analyses:
                    # Only include items with deep_dive and suggested_updates
                    deep_dive = item.get("deep_dive", {})
                    site_relevance = deep_dive.get("site_relevance", {})
                    suggested_updates = site_relevance.get("suggested_updates", [])

                    if suggested_updates:
                        item["_week"] = week
                        item["_file"] = file_path.name
                        all_items.append(item)

                print(f"  Loaded {len(analyses)} items from {file_path.name}")
        except Exception as e:
            print(f"  Warning: Failed to load {file_path.name}: {e}")

    return all_items


def load_topic_page(project_root: Path, topic_slug: str) -> dict:
    """Load and parse a topic page to understand its structure."""
    file_path = TOPIC_PAGE_MAP.get(topic_slug)
    if not file_path:
        return {"exists": False, "slug": topic_slug}

    full_path = project_root / file_path
    if not full_path.exists():
        return {"exists": False, "slug": topic_slug, "path": file_path}

    try:
        content = full_path.read_text(encoding="utf-8")

        # Extract section headings (h2 and h3)
        h2_pattern = r'<h2[^>]*>([^<]+)</h2>'
        h3_pattern = r'<h3[^>]*>([^<]+)</h3>'

        sections = []
        for match in re.finditer(h2_pattern, content):
            sections.append({"level": 2, "title": match.group(1).strip()})
        for match in re.finditer(h3_pattern, content):
            sections.append({"level": 3, "title": match.group(1).strip()})

        # Check for CodeBlock usage
        has_code_blocks = "CodeBlock" in content

        return {
            "exists": True,
            "slug": topic_slug,
            "path": file_path,
            "sections": sections,
            "has_code_blocks": has_code_blocks,
            "content_length": len(content),
        }
    except Exception as e:
        return {"exists": False, "slug": topic_slug, "path": file_path, "error": str(e)}


# =============================================================================
# Confidence Scoring
# =============================================================================


def calculate_confidence(item: dict) -> float:
    """
    Calculate confidence score for an item.

    Formula:
        confidence = (bulk_score / 10) * 0.4 +
                     quality_score * 0.4 +
                     source_weight * 0.2

    Where:
        - bulk_score: From Tier 1 analysis (0-10)
        - quality_score: Has code/techniques/applications (0-1)
        - source_weight: paper=1.0, article=0.8, video=0.7, repo=0.6
    """
    tier1 = item.get("tier1_analysis", {})
    deep_dive = item.get("deep_dive", {})

    # Bulk score component (40%)
    bulk_score = tier1.get("bulk_score", 5)
    bulk_component = (bulk_score / 10) * 0.4

    # Quality score component (40%)
    quality_indicators = 0
    quality_max = 4

    # Has techniques documented
    if deep_dive.get("techniques"):
        quality_indicators += 1

    # Has code snippets
    if deep_dive.get("code_snippets"):
        quality_indicators += 1

    # Has practical applications
    if deep_dive.get("practical_applications"):
        quality_indicators += 1

    # Has key contribution
    if deep_dive.get("key_contribution"):
        quality_indicators += 1

    quality_score = quality_indicators / quality_max
    quality_component = quality_score * 0.4

    # Source weight component (20%)
    item_type = item.get("type", "article")
    source_weight = SOURCE_WEIGHTS.get(item_type, 0.5)
    source_component = source_weight * 0.2

    confidence = bulk_component + quality_component + source_component
    return round(confidence, 2)


# =============================================================================
# Content Generation
# =============================================================================


def generate_content_update(
    suggestion: dict,
    item: dict,
    page_info: dict,
    client: anthropic.Anthropic,
    dry_run: bool = False,
) -> dict:
    """Generate content update using Claude."""
    if dry_run:
        return {
            "prose": "[DRY-RUN] This would be the generated prose content.",
            "code_example": {
                "pseudo": "// Pseudo-code would go here",
                "python": "# Python (LangChain) would go here",
                "csharp": "// C# (Agent Framework) would go here",
            },
            "callout": None,
        }

    deep_dive = item.get("deep_dive", {})
    tier1 = item.get("tier1_analysis", {})

    # Build context for Claude
    existing_sections = ""
    if page_info.get("sections"):
        existing_sections = "\n".join(
            [f"- {s['title']} (h{s['level']})" for s in page_info["sections"]]
        )

    prompt = f"""You are generating content for an AI agents educational site. Generate content for a suggested update.

SOURCE MATERIAL:
- Title: {item.get('title', 'Unknown')}
- Type: {item.get('type', 'unknown')}
- URL: {item.get('url', '')}
- Key Contribution: {deep_dive.get('key_contribution', 'N/A')}
- Techniques: {json.dumps(deep_dive.get('techniques', []), indent=2)}
- Code Snippets: {json.dumps(deep_dive.get('code_snippets', [])[:2], indent=2)}

SUGGESTED UPDATE:
- Target Page: {suggestion.get('page', '')}
- Target Section: {suggestion.get('section', '')}
- Suggestion: {suggestion.get('suggestion', '')}

EXISTING PAGE SECTIONS:
{existing_sections or 'Not available'}

{FRAMEWORK_STANDARDS}

Generate content in JSON format:
{{
  "prose": "2-3 paragraphs of educational content that fits the site's style. Reference the source but focus on the technique/pattern, not the paper itself. Write in active voice, be concise.",
  "code_example": {{
    "pseudo": "Clean pseudo-code showing the core concept (10-20 lines)",
    "python": "Python implementation using LangChain/LangGraph patterns (20-40 lines)",
    "csharp": "C# implementation using Microsoft Agent Framework patterns (20-40 lines)"
  }},
  "callout": {{
    "type": "info|tip|warning",
    "title": "Short title",
    "content": "One sentence insight or tip"
  }}
}}

If code examples aren't applicable, set code_example to null.
If no callout is needed, set callout to null.
Focus on practical, actionable content that developers can use."""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=3000,
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
        print(f"    Warning: Content generation failed: {e}")
        return {
            "prose": f"[GENERATION FAILED: {e}]",
            "code_example": None,
            "callout": None,
            "error": str(e),
        }


# =============================================================================
# PR Formatting
# =============================================================================


def format_code_example_details(code_example: dict) -> str:
    """Format code examples as collapsible details block."""
    if not code_example:
        return ""

    lines = ["<details>", "<summary>Code Examples (click to expand)</summary>", ""]

    if code_example.get("pseudo"):
        lines.extend([
            "**Pseudo-code:**",
            "```",
            code_example["pseudo"],
            "```",
            "",
        ])

    if code_example.get("python"):
        lines.extend([
            "**Python (LangChain):**",
            "```python",
            code_example["python"],
            "```",
            "",
        ])

    if code_example.get("csharp"):
        lines.extend([
            "**C# (Agent Framework):**",
            "```csharp",
            code_example["csharp"],
            "```",
            "",
        ])

    lines.append("</details>")
    return "\n".join(lines)


def format_pr_body(suggestions: list[dict], week: str, stats: dict) -> str:
    """Format the PR body with all suggestions."""
    lines = [
        "## Auto-generated Content Update",
        "",
        f"**Week:** {week}",
        f"**Sources analyzed:** {stats.get('sources_analyzed', 0)}",
        f"**Suggestions generated:** {len(suggestions)}",
        "",
        "---",
        "",
    ]

    # Group suggestions by topic
    by_topic = {}
    for s in suggestions:
        topic = s.get("topic", "unknown")
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(s)

    for topic, topic_suggestions in by_topic.items():
        file_path = TOPIC_PAGE_MAP.get(topic, f"src/pages/topics/{topic}/index.astro")
        lines.extend([
            f"### Topic: `{topic}`",
            f"**File:** `{file_path}`",
            "",
        ])

        for i, s in enumerate(topic_suggestions, 1):
            item = s.get("item", {})
            content = s.get("content", {})

            lines.extend([
                f"#### Change {i}: {s.get('section', 'New Section')}",
                f"**Source:** [{item.get('title', 'Unknown')}]({item.get('url', '#')})",
                f"**Confidence:** {s.get('confidence', 0):.2f}",
                f"**Type:** {item.get('type', 'unknown')}",
                "",
            ])

            # Prose
            if content.get("prose"):
                lines.extend([
                    "**Suggested prose:**",
                    "",
                    content["prose"],
                    "",
                ])

            # Code examples
            if content.get("code_example"):
                lines.append(format_code_example_details(content["code_example"]))
                lines.append("")

            # Callout
            if content.get("callout"):
                callout = content["callout"]
                lines.extend([
                    "**Suggested callout:**",
                    f"> **{callout.get('type', 'info').upper()}: {callout.get('title', '')}**",
                    f"> {callout.get('content', '')}",
                    "",
                ])

            lines.append("---")
            lines.append("")

    # Review guidelines
    lines.extend([
        "## Review Guidelines",
        "",
        "- [ ] Verify technical accuracy of suggested content",
        "- [ ] Check code examples compile/run correctly",
        "- [ ] Ensure content fits the page structure and style",
        "- [ ] Verify source links are correct and accessible",
        "- [ ] Consider if content should be in a different section",
        "",
        "---",
        "",
        "*Generated by content-agent*",
    ])

    return "\n".join(lines)


# =============================================================================
# Git/PR Operations
# =============================================================================


def run_git_command(args: list[str], cwd: Path = None) -> tuple[bool, str]:
    """Run a git command and return success status and output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def create_branch_and_pr(
    suggestions: list[dict],
    week: str,
    stats: dict,
    project_root: Path,
    dry_run: bool = False,
) -> str:
    """Create a branch and PR with the suggestions."""
    branch_name = f"content-update/{week}"
    pr_title = f"Content Update: {week}"

    if dry_run:
        print(f"\n[DRY-RUN] Would create:")
        print(f"  Branch: {branch_name}")
        print(f"  PR Title: {pr_title}")
        print(f"  Suggestions: {len(suggestions)}")
        return "[DRY-RUN] PR URL would be here"

    # Check if branch already exists
    success, output = run_git_command(
        ["branch", "--list", branch_name],
        cwd=project_root,
    )
    if output:
        print(f"  Branch {branch_name} already exists, deleting...")
        run_git_command(["branch", "-D", branch_name], cwd=project_root)

    # Create and checkout branch
    print(f"  Creating branch: {branch_name}")
    success, output = run_git_command(
        ["checkout", "-b", branch_name],
        cwd=project_root,
    )
    if not success:
        print(f"  Error creating branch: {output}")
        return ""

    # Create a placeholder file to have something to commit
    suggestions_file = project_root / "src" / "data" / "content-suggestions" / f"{week}.json"
    suggestions_file.parent.mkdir(parents=True, exist_ok=True)

    suggestions_data = {
        "week": week,
        "generated_at": datetime.now().isoformat(),
        "stats": stats,
        "suggestions": [
            {
                "topic": s.get("topic"),
                "section": s.get("section"),
                "confidence": s.get("confidence"),
                "source_title": s.get("item", {}).get("title"),
                "source_url": s.get("item", {}).get("url"),
                "source_type": s.get("item", {}).get("type"),
            }
            for s in suggestions
        ],
    }

    with open(suggestions_file, "w") as f:
        json.dump(suggestions_data, f, indent=2)

    # Stage and commit
    run_git_command(["add", str(suggestions_file)], cwd=project_root)
    commit_message = f"Content suggestions for {week}\n\nGenerated {len(suggestions)} content update suggestions."
    run_git_command(
        ["commit", "-m", commit_message],
        cwd=project_root,
    )

    # Push branch
    print(f"  Pushing branch...")
    success, output = run_git_command(
        ["push", "-u", "origin", branch_name],
        cwd=project_root,
    )
    if not success:
        print(f"  Error pushing: {output}")
        return ""

    # Create PR using gh CLI
    print(f"  Creating PR...")
    pr_body = format_pr_body(suggestions, week, stats)

    try:
        result = subprocess.run(
            [
                "gh", "pr", "create",
                "--title", pr_title,
                "--body", pr_body,
                "--base", "main",
                "--head", branch_name,
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        pr_url = result.stdout.strip()
        print(f"  PR created: {pr_url}")
        return pr_url

    except subprocess.CalledProcessError as e:
        print(f"  Error creating PR: {e.stderr}")
        return ""
    except FileNotFoundError:
        print("  Error: gh CLI not found. Install with: https://cli.github.com/")
        return ""


# =============================================================================
# Main Logic
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Content Agent: Generate PRs with content update suggestions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview without creating PR (default for safety)",
    )
    parser.add_argument(
        "--create-pr",
        action="store_true",
        help="Actually create the PR (disables dry-run)",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=DEFAULT_WEEKS,
        help=f"Number of weeks to process (default: {DEFAULT_WEEKS})",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=DEFAULT_CONFIDENCE_THRESHOLD,
        help=f"Minimum confidence threshold 0.0-1.0 (default: {DEFAULT_CONFIDENCE_THRESHOLD})",
    )
    parser.add_argument(
        "--max-suggestions",
        type=int,
        default=DEFAULT_MAX_SUGGESTIONS,
        help=f"Maximum suggestions per PR (default: {DEFAULT_MAX_SUGGESTIONS})",
    )
    args = parser.parse_args()

    # --create-pr overrides --dry-run
    dry_run = args.dry_run and not args.create_pr

    print("Content Agent starting...")
    print(f"  Dry-run: {dry_run}")
    print(f"  Weeks: {args.weeks}")
    print(f"  Min confidence: {args.min_confidence}")
    print(f"  Max suggestions: {args.max_suggestions}")
    print()

    # Validate API key
    if not dry_run:
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not anthropic_key:
            print("ERROR: ANTHROPIC_API_KEY environment variable not set")
            sys.exit(1)
        client = anthropic.Anthropic()
    else:
        client = None

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    deep_dives_dir = project_root / "src" / "data" / "deep-dives"

    # Load deep dive results
    print("Loading deep dive results...")
    items = load_deep_dives(deep_dives_dir, args.weeks)
    print(f"Total items with suggestions: {len(items)}")

    if not items:
        print("No items with suggested updates found.")
        return

    # Calculate confidence and filter
    print("\nCalculating confidence scores...")
    scored_items = []
    for item in items:
        confidence = calculate_confidence(item)
        if confidence >= args.min_confidence:
            item["_confidence"] = confidence
            scored_items.append(item)
        else:
            print(f"  Skipped (confidence {confidence:.2f}): {item.get('title', 'Unknown')[:50]}")

    print(f"Items passing confidence threshold: {len(scored_items)}")

    if not scored_items:
        print("No items passed the confidence threshold.")
        return

    # Sort by confidence and limit
    scored_items.sort(key=lambda x: x.get("_confidence", 0), reverse=True)

    # Extract suggestions from items
    print("\nExtracting suggestions...")
    all_suggestions = []

    for item in scored_items:
        deep_dive = item.get("deep_dive", {})
        site_relevance = deep_dive.get("site_relevance", {})
        suggested_updates = site_relevance.get("suggested_updates", [])

        for update in suggested_updates:
            # Extract topic from page path
            page = update.get("page", "")
            topic_match = re.search(r"/topics/([^/]+)/", page)
            topic = topic_match.group(1) if topic_match else "unknown"

            suggestion = {
                "topic": topic,
                "page": page,
                "section": update.get("section", ""),
                "suggestion_text": update.get("suggestion", ""),
                "confidence": item.get("_confidence", 0),
                "item": {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "type": item.get("type", ""),
                    "source": item.get("source", ""),
                },
                "deep_dive": deep_dive,
            }
            all_suggestions.append(suggestion)

            if len(all_suggestions) >= args.max_suggestions:
                break

        if len(all_suggestions) >= args.max_suggestions:
            break

    print(f"Total suggestions: {len(all_suggestions)}")

    # Generate content for each suggestion
    print("\nGenerating content updates...")
    for i, suggestion in enumerate(all_suggestions):
        print(f"  [{i + 1}/{len(all_suggestions)}] {suggestion['topic']}: {suggestion['section'][:40]}...")

        # Load topic page info
        page_info = load_topic_page(project_root, suggestion["topic"])

        # Generate content
        content = generate_content_update(
            suggestion,
            {"title": suggestion["item"]["title"], "url": suggestion["item"]["url"],
             "type": suggestion["item"]["type"], "deep_dive": suggestion["deep_dive"]},
            page_info,
            client,
            dry_run,
        )
        suggestion["content"] = content

    # Determine week for PR
    current_week = get_week_string()

    # Stats
    stats = {
        "sources_analyzed": len(items),
        "passed_threshold": len(scored_items),
        "suggestions_generated": len(all_suggestions),
        "confidence_threshold": args.min_confidence,
    }

    # Create PR or show preview
    if dry_run:
        print("\n" + "=" * 60)
        print("DRY-RUN PREVIEW")
        print("=" * 60)
        print(format_pr_body(all_suggestions, current_week, stats))
        print("=" * 60)
        print("\nTo create the PR, run with --create-pr flag")
    else:
        print("\nCreating PR...")
        pr_url = create_branch_and_pr(
            all_suggestions,
            current_week,
            stats,
            project_root,
            dry_run,
        )
        if pr_url:
            print(f"\nPR created successfully: {pr_url}")
        else:
            print("\nFailed to create PR")
            sys.exit(1)


if __name__ == "__main__":
    main()
