#!/usr/bin/env python3
"""
add-article.py — Generate newspaper-style MDX articles using Claude with web search

Usage:
    python scripts/add-article.py "MCP server discovery"
    python scripts/add-article.py --url "https://..."
    python scripts/add-article.py --tweet "tweet text"
    python scripts/add-article.py --text "pasted article or notes"
    python scripts/add-article.py "topic" --commit
    python scripts/add-article.py "topic" --featured --commit

Requires: ANTHROPIC_API_KEY env var
         pip install anthropic python-slugify
"""

import os
import re
import sys
import json
import argparse
import subprocess
from datetime import date
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)

try:
    from slugify import slugify
except ImportError:
    def slugify(text: str) -> str:
        """Basic slugify fallback."""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text.strip('-')

ROOT = Path(__file__).parent.parent
ARTICLES_DIR = ROOT / "src" / "content" / "articles"

CATEGORIES = [
    "Foundational", "Context Layer", "Advanced", "Protocols", "Safety", "Evaluation"
]

SYSTEM_PROMPT = f"""You are a senior editor at a newspaper covering AI agent engineering for practitioners.

Your task is to write a well-researched, newspaper-style MDX article.

## Output Format

Output ONLY valid MDX starting with `---` frontmatter. No preamble, no explanation, no markdown code fences around the output.

## Frontmatter Schema

```
---
title: "Article Title"
description: "One sentence, 15-25 words, written as an italic newspaper lede."
category: "<one of: {', '.join(CATEGORIES)}>"
date: "{date.today().isoformat()}"
type: "article"
source_url: "<if based on a URL, include it; otherwise omit>"
tags:
  - tag1
  - tag2
  - tag3
featured: false
---
```

## Article Rules

1. **Length**: 800–1500 words of flowing prose (not counting code blocks or component markup).
2. **Prose style**: Clear, direct, authoritative — like The Economist covering technology. No hype. Facts first.
3. **Structure**: Use `##` for major sections, `###` for subsections.
4. **First paragraph**: MUST be pure prose — no heading, no component, no code block. This enables the drop-cap rendering.
5. **Lists**: Convert any bullet points into flowing prose paragraphs.
6. **Code**: Include at most 1–2 Python code examples as fenced ```python blocks where technically relevant.
7. **Components** (use as JSX, no imports needed):
   - `<Callout type="info|warning|tip|danger" title="...">prose content</Callout>`
   - `<Diagram title="...">ascii art here</Diagram>`
   - `<Table caption="..."><thead>...</thead><tbody>...</tbody></Table>`
8. **Links**: Use absolute paths like `/articles/topic-slug/` for internal links.
9. **No dark mode**: No `dark:` Tailwind classes anywhere.
10. Use `<Callout>` at least once, preferably twice, to highlight key insights or warnings.

## Research

Use the web_search tool to find current, accurate information before writing. Prefer recent sources (2024–2025). Cite facts in context rather than in a bibliography."""


def build_user_message(args) -> str:
    """Build the user message from CLI arguments."""
    if args.url:
        return f"Write a newspaper-style article about the following URL. Research it first, then write.\n\nURL: {args.url}"
    elif args.tweet:
        return f"Write a newspaper-style article expanding on this tweet/social post:\n\n{args.tweet}"
    elif args.text:
        return f"Write a newspaper-style article based on the following notes/pasted article:\n\n{args.text}"
    else:
        return f"Write a newspaper-style article about: {args.topic}"


def extract_slug_from_title(title: str) -> str:
    """Extract a URL-friendly slug from the article title."""
    # Remove special characters, convert to lowercase hyphenated
    return slugify(title)[:60]


def extract_frontmatter_title(mdx_content: str) -> str | None:
    """Extract title from MDX frontmatter."""
    match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', mdx_content, re.MULTILINE)
    return match.group(1).strip().strip('"\'') if match else None


def generate_article(client: anthropic.Anthropic, user_message: str) -> str:
    """Call Claude with web search to generate the article."""
    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
        }
    ]

    # Stream the response to show progress
    print("  Researching and writing...", flush=True)

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8096,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=[{"role": "user", "content": user_message}],
    )

    # Extract text content from the response
    text_parts = [
        block.text for block in message.content
        if hasattr(block, 'text')
    ]

    return "\n".join(text_parts).strip()


def save_article(slug: str, content: str, featured: bool = False) -> Path:
    """Save MDX content to the articles directory."""
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ARTICLES_DIR / f"{slug}.mdx"
    if out_path.exists():
        raise FileExistsError(f"Article already exists: {out_path}. Use --slug to specify a different name.")

    # Inject featured flag if requested
    if featured:
        content = re.sub(r'(?m)^featured:\s*false\s*$', 'featured: true', content, count=1)

    out_path.write_text(content, encoding="utf-8")
    return out_path


def git_commit(slug: str, title: str) -> bool:
    """Stage and commit the new article file."""
    file_path = ARTICLES_DIR / f"{slug}.mdx"
    try:
        subprocess.run(
            ["git", "add", str(file_path)],
            cwd=ROOT, check=True, capture_output=True
        )
        safe_title = title.replace("\n", " ").replace("\r", " ")[:120]
        subprocess.run(
            ["git", "commit", "-m", f"Add article: {safe_title}"],
            cwd=ROOT, check=True, capture_output=True
        )
        print(f"  Committed: {file_path.relative_to(ROOT)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Git error: {e.stderr.decode() if e.stderr else '(no stderr)'}")
        return False


def validate_mdx(content: str) -> list[str]:
    """Return warnings about MDX content quality."""
    warnings = []
    if not content.startswith("---"):
        warnings.append("Missing frontmatter")
        return warnings  # No point checking fields if frontmatter is missing
    # Extract only the frontmatter block to avoid false positives from code snippets
    end = content.find("---", 3)
    frontmatter = content[:end] if end != -1 else content
    required = ["title:", "description:", "category:", "date:", "type:", "tags:", "featured:"]
    for f in required:
        if f not in frontmatter:
            warnings.append(f"Missing field: {f}")
    if "dark:" in content:
        warnings.append("Contains dark: classes")
    if len(content) < 1000:
        warnings.append("Article seems very short")
    return warnings


def main():
    parser = argparse.ArgumentParser(
        description="Generate newspaper-style MDX articles using Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/add-article.py "MCP server discovery patterns"
  python scripts/add-article.py --url "https://arxiv.org/abs/2412.xxxxx"
  python scripts/add-article.py --tweet "Just released: agents can now..."
  python scripts/add-article.py "computer use agents" --featured --commit
"""
    )

    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--url", help="Generate article about this URL")
    input_group.add_argument("--tweet", help="Expand a tweet/social post into an article")
    input_group.add_argument("--text", help="Generate article from pasted text/notes")

    parser.add_argument("topic", nargs="?", help="Topic string to research and write about")
    parser.add_argument("--commit", action="store_true", help="Auto-commit the generated file")
    parser.add_argument("--featured", action="store_true", help="Mark article as featured on homepage")
    parser.add_argument("--slug", help="Override auto-generated slug")
    parser.add_argument("--dry-run", action="store_true", help="Print article, don't save")

    args = parser.parse_args()

    # Validate input
    if not any([args.topic, args.url, args.tweet, args.text]):
        parser.error("Provide a topic, --url, --tweet, or --text")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print(f"\nGenerating article...")
    if args.topic:
        print(f"  Topic: {args.topic}")
    elif args.url:
        print(f"  URL: {args.url}")
    elif args.tweet:
        print(f"  Tweet: {args.tweet[:80]}...")

    user_message = build_user_message(args)

    try:
        mdx_content = generate_article(client, user_message)
    except Exception as e:
        print(f"\nERROR generating article: {e}")
        sys.exit(1)

    # Determine slug
    title = extract_frontmatter_title(mdx_content) or args.topic or "untitled"
    if title == "untitled" and not args.slug:
        print("\nWARNING: Could not extract title from frontmatter. Use --slug to avoid overwriting previous untitled articles.")
    slug = args.slug or extract_slug_from_title(title)

    # Validate
    warnings = validate_mdx(mdx_content)

    if args.dry_run:
        print(f"\n{'='*60}\nDRY RUN: {slug}.mdx\n{'='*60}\n")
        print(mdx_content)
        if warnings:
            print(f"\nWarnings: {warnings}")
        return

    # Save
    out_path = save_article(slug, mdx_content, featured=args.featured)
    print(f"\n  Saved → {out_path.relative_to(ROOT)}")

    if warnings:
        print(f"  Warnings: {', '.join(warnings)}")

    if args.commit:
        git_commit(slug, title)

    print(f"\nDone! View at: /articles/{slug}/")
    print(f"Run `npm run dev` to preview.")


if __name__ == "__main__":
    main()
