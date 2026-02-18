#!/usr/bin/env python3
"""
migrate-topics.py — one-time migration of all .astro topic pages to MDX

Usage:
    python scripts/migrate-topics.py
    python scripts/migrate-topics.py --slug tool-use   # single topic
    python scripts/migrate-topics.py --dry-run         # print MDX, don't save

Requires: ANTHROPIC_API_KEY env var
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
TOPICS_DIR = ROOT / "src" / "pages" / "topics"
ARTICLES_DIR = ROOT / "src" / "content" / "articles"

# Slug → (category, date, tags) — pre-assigned metadata
TOPIC_META = {
    "tool-use":             ("Foundational",    "2024-01-15", ["tool-use", "function-calling", "llm"]),
    "react-pattern":        ("Foundational",    "2024-01-20", ["react", "reasoning", "agentic-loop"]),
    "memory":               ("Foundational",    "2024-02-01", ["memory", "context", "embeddings"]),
    "context-engineering":  ("Context Layer",   "2024-02-10", ["context-window", "prompting", "optimization"]),
    "context-bloat":        ("Context Layer",   "2024-02-15", ["context-rot", "degradation", "performance"]),
    "prompt-caching":       ("Context Layer",   "2024-02-20", ["caching", "kv-cache", "latency", "cost"]),
    "skills-pattern":       ("Advanced",        "2024-03-01", ["skills", "tool-management", "token-savings"]),
    "mcp":                  ("Protocols",       "2024-03-10", ["mcp", "protocol", "anthropic", "integration"]),
    "a2a":                  ("Protocols",       "2024-03-15", ["a2a", "agent-communication", "google"]),
    "mcp-apps":             ("Protocols",       "2024-03-20", ["mcp", "ui", "interactive", "apps"]),
    "ucp":                  ("Protocols",       "2024-03-25", ["commerce", "protocol", "checkout", "agents"]),
    "learning-adaptation":  ("Advanced",        "2024-04-01", ["learning", "reflexion", "self-improvement"]),
    "agent-fine-tuning":    ("Advanced",        "2024-04-10", ["fine-tuning", "training", "llm", "gpu"]),
    "multi-agent":          ("Advanced",        "2024-04-15", ["multi-agent", "orchestration", "coordination"]),
    "agentic-rag":          ("Advanced",        "2024-04-20", ["rag", "retrieval", "self-rag", "graph-rag"]),
    "safety":               ("Safety",          "2024-05-01", ["safety", "guardrails", "owasp", "security"]),
    "evaluation":           ("Evaluation",      "2024-05-10", ["evaluation", "metrics", "benchmarks", "llm-judge"]),
}

SYSTEM_PROMPT = """You are a technical editor converting Astro topic pages into newspaper-style MDX articles.

Rules:
1. Output ONLY valid MDX — start with --- frontmatter, no preamble, no explanation.
2. Frontmatter must have exactly these fields:
   title: (string)
   description: (one-sentence italic lede, 15–25 words)
   category: (provided)
   date: (provided)
   type: 'topic'
   tags: (provided as YAML list)
   featured: false

3. PROSE: Convert all section content to flowing, 3–6 sentence paragraphs. NO bullet lists in prose sections — fold list items into flowing sentences.

4. HEADINGS: Use ## for major sections, ### for subsections.

5. CODE: Keep only the Python tab from any CodeBlock. Output as fenced ```python blocks. Drop pseudo-code and C# tabs entirely.

6. COMPONENTS: Keep these as JSX (no imports needed — they are injected):
   - <Callout type="info|warning|tip|danger" title="...">content</Callout>
   - <Diagram title="...">ascii art</Diagram>
   - <Table caption="..."><thead>...</thead><tbody>...</tbody></Table>
   Table inner content stays as HTML table rows/cells.

7. LINKS: Change /topics/[slug]/ to /articles/[slug]/ throughout.

8. REMOVE: All dark: classes, primary-* colors, Astro frontmatter, import statements, Astro-specific syntax.

9. FIRST PARAGRAPH: Must be pure prose (enables drop cap in the renderer). Do not start with a heading or component.

10. LENGTH: 600–1200 words of prose (excluding code blocks).

Output the raw MDX file content, nothing else."""


def read_astro_file(slug: str) -> str:
    path = TOPICS_DIR / slug / "index.astro"
    if not path.exists():
        raise FileNotFoundError(f"No topic file at {path}")
    return path.read_text(encoding="utf-8")


def convert_to_mdx(client: anthropic.Anthropic, slug: str, astro_content: str) -> str:
    meta = TOPIC_META.get(slug, ("General", "2024-01-01", [slug]))
    category, date, tags = meta

    tags_yaml = "\n".join(f"  - {t}" for t in tags)

    user_message = f"""Convert this Astro topic page to MDX.

Frontmatter metadata to use:
  category: {category}
  date: {date}
  tags:
{tags_yaml}

Astro source:
---
{astro_content}
---"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text_blocks = [b.text for b in message.content if hasattr(b, "text")]
    if not text_blocks:
        raise ValueError("API returned no text content")
    return text_blocks[0].strip()


def save_mdx(slug: str, content: str) -> Path:
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ARTICLES_DIR / f"{slug}.mdx"
    out_path.write_text(content, encoding="utf-8")
    return out_path


def validate_mdx(content: str, slug: str) -> list[str]:
    """Return list of warnings about the MDX content."""
    warnings = []

    if not content.startswith("---"):
        warnings.append("Missing frontmatter (does not start with ---)")

    required_fields = ["title:", "description:", "category:", "date:", "type:", "tags:", "featured:"]
    for field in required_fields:
        if field not in content:
            warnings.append(f"Missing frontmatter field: {field}")

    if "dark:" in content:
        warnings.append("Contains dark: classes (should have been removed)")

    if "primary-" in content:
        warnings.append("Contains primary-* color classes (should have been removed)")

    if "import " in content and "```" not in content:
        warnings.append("May contain import statements outside code blocks")

    return warnings


def main():
    parser = argparse.ArgumentParser(description="Migrate Astro topic pages to MDX")
    parser.add_argument("--slug", help="Migrate only this slug (e.g. tool-use)")
    parser.add_argument("--dry-run", action="store_true", help="Print MDX to stdout, don't save")
    parser.add_argument("--delete-originals", action="store_true",
                        help="Delete src/pages/topics/[slug]/ directories after migration")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Determine which slugs to process
    if args.slug:
        slugs = [args.slug]
    else:
        slugs = sorted([d.name for d in TOPICS_DIR.iterdir()
                       if d.is_dir() and (d / "index.astro").exists()])

    print(f"Migrating {len(slugs)} topic(s): {', '.join(slugs)}\n")

    results = {"success": [], "error": [], "warnings": {}}

    for slug in slugs:
        print(f"  [{slug}] Reading...", end=" ", flush=True)
        try:
            astro_content = read_astro_file(slug)
        except FileNotFoundError as e:
            print(f"SKIP — {e}")
            results["error"].append(slug)
            continue

        print("Converting...", end=" ", flush=True)
        try:
            mdx_content = convert_to_mdx(client, slug, astro_content)
        except Exception as e:
            print(f"ERROR — {e}")
            results["error"].append(slug)
            continue

        warnings = validate_mdx(mdx_content, slug)

        if args.dry_run:
            print(f"\n{'='*60}\n{slug}.mdx\n{'='*60}")
            print(mdx_content[:2000])
            if len(mdx_content) > 2000:
                print(f"... [{len(mdx_content)} total chars]")
        else:
            out_path = save_mdx(slug, mdx_content)
            print(f"Saved → {out_path.relative_to(ROOT)}", end="")
            results["success"].append(slug)

        if warnings:
            results["warnings"][slug] = warnings
            print(f" ⚠ {len(warnings)} warning(s)")
        else:
            print(" ✓")

    # Delete originals if requested — requires explicit confirmation
    if args.delete_originals and not args.dry_run:
        dirs_to_delete = [TOPICS_DIR / s for s in results["success"] if (TOPICS_DIR / s).exists()]
        if dirs_to_delete:
            print(f"\nAbout to permanently delete {len(dirs_to_delete)} topic director(ies):")
            for d in dirs_to_delete:
                print(f"  {d.relative_to(ROOT)}")
            confirm = input("Type 'yes' to confirm deletion: ").strip().lower()
            if confirm != "yes":
                print("Deletion cancelled.")
            else:
                import shutil
                for d in dirs_to_delete:
                    shutil.rmtree(d)
                    print(f"  Deleted {d.relative_to(ROOT)}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Done: {len(results['success'])} succeeded, {len(results['error'])} failed")
    if results["warnings"]:
        print("\nWarnings:")
        for slug, warns in results["warnings"].items():
            for w in warns:
                print(f"  [{slug}] {w}")
    if results["error"]:
        print(f"\nFailed slugs: {', '.join(results['error'])}")


if __name__ == "__main__":
    main()
