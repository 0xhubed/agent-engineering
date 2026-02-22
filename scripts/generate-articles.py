#!/usr/bin/env python3
"""
Evaluate Twitter-sourced articles from news.json and generate MDX topic pages.

For each Twitter item in news.json:
1. Re-fetch full article content
2. Ask Claude to evaluate quality and (if worthy) generate MDX
3. Save to src/content/articles/{slug}.mdx
4. Open a PR for human review

Runs after update-news.py in CI, or manually:
    python scripts/generate-articles.py
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import httpx

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ARTICLES_DIR_RELATIVE = "src/content/articles"

MDX_GENERATION_PROMPT = """\
You are a technical writer for a developer-focused site about AI agent engineering.
You have two jobs: (1) evaluate whether a source article covers a topic worth writing
about, and (2) if so, write an entirely original educational article on that topic.

## Site context
The site covers AI agent patterns: tool use, ReAct, memory, multi-agent orchestration,
MCP/A2A protocols, evaluation, RAG, prompt engineering, and related engineering topics.
The audience is software engineers building production AI agent systems.

## Existing articles (avoid duplicating these topics)
{existing_articles}

## Step 1 — Evaluate the source article
Use the source text to decide whether the topic is worth covering. A topic is WORTHY
if ALL of the following apply:
- Covers a specific, well-defined engineering concept or pattern (not a product launch or opinion)
- Has enough technical substance to support 400–800 words of original prose
- Not already covered by an existing article listed above
- Likely to stay relevant for 6+ months (not a version announcement)

## Step 2 — Write an original article (only if worthy=true)
Write a completely original educational article about the concept the source covers.

**Important:** The source tells you *what topic* to write about — do not reproduce,
paraphrase, or closely follow its structure or wording. Write as an independent
expert explaining the concept to engineers from first principles.

### MDX body instructions
- Start with a 2–3 sentence intro paragraph (no heading)
- Use 3–5 `## h2` sections with flowing, factual prose
- Use `<Callout type="info|tip|warning">` for key insights (at least one)
- Use `<Diagram>` with ASCII art for architecture/flow diagrams where helpful
- Use fenced code blocks (plain markdown) for code examples
- No marketing language; measured, factual tone
- Do NOT include frontmatter — the script adds it
- Do NOT add any attribution footer, source note, or disclaimer at the end of the article body. The script appends standardized attribution automatically.

## Source article to evaluate
URL: {url}

Full text (may be truncated — used for topic evaluation only):
{article_text}

## Response format (JSON only, no markdown wrapper)
{{
  "worthy": true or false,
  "reason": "one sentence explaining the decision",
  "slug": "kebab-case-slug (only if worthy=true)",
  "title": "Article title (only if worthy=true)",
  "description": "One sentence for listing pages (only if worthy=true)",
  "category": "Foundational | Infrastructure | Advanced | Evaluation (only if worthy=true)",
  "tags": ["tag1", "tag2"] (only if worthy=true),
  "source_title": "Title of the source article as written by its authors (only if worthy=true)",
  "authors": "Author names from the source article, comma-separated, or empty string if not found (only if worthy=true)",
  "mdx_content": "Full original MDX body — no frontmatter, no attribution footer (only if worthy=true)"
}}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_news_items(project_root: Path) -> list[dict]:
    """Load items from news.json."""
    news_file = project_root / "src" / "data" / "news.json"
    if not news_file.exists():
        print("news.json not found — nothing to process.")
        return []
    with open(news_file) as f:
        return json.load(f).get("items", [])


def twitter_candidates(items: list[dict]) -> list[dict]:
    """Filter to items sourced from Twitter/X accounts."""
    return [item for item in items if item.get("source", "").startswith("@")]


def load_existing_articles(articles_dir: Path) -> list[dict]:
    """Return list of {slug, title, source_url} for all existing MDX files."""
    results = []
    for mdx_file in sorted(articles_dir.glob("*.mdx")):
        slug = mdx_file.stem
        title = slug  # fallback
        source_url = None
        try:
            content = mdx_file.read_text()
            for line in content.splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("source_url:"):
                    source_url = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("---") and title != slug:
                    break  # past frontmatter
        except Exception:
            pass
        results.append({"slug": slug, "title": title, "source_url": source_url})
    return results


def fetch_full_article(url: str) -> str | None:
    """Fetch URL and return extracted plain text (max 6 000 chars)."""
    from html.parser import HTMLParser

    class _TextExtractor(HTMLParser):
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

    try:
        resp = httpx.get(
            url,
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "AgentEngineering-ArticleBot/1.0"},
        )
        resp.raise_for_status()
        extractor = _TextExtractor()
        extractor.feed(resp.text)
        text = extractor.get_text()
        return text[:6000] if text else None
    except Exception as e:
        print(f"    Could not fetch {url}: {e}")
        return None


def evaluate_and_generate(
    client: anthropic.Anthropic,
    url: str,
    article_text: str,
    existing_articles: list[dict],
) -> dict | None:
    """Call Claude to evaluate quality and (if worthy) generate MDX content."""
    existing_summary = "\n".join(
        f"- {a['slug']}: {a['title']}" for a in existing_articles
    )
    prompt = MDX_GENERATION_PROMPT.format(
        existing_articles=existing_summary or "(none yet)",
        url=url,
        article_text=article_text,
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"    JSON parse error: {e}")
        print(f"    Raw response: {text[:500]}")
        return None


def _yaml_str(s: str) -> str:
    """Escape a string for use inside a YAML double-quoted scalar."""
    return s.strip().replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")


def assemble_mdx(result: dict, url: str, today: str, shared_by: str = "") -> str:
    """Build the full MDX file content from Claude's response."""
    tags = result.get("tags", [])
    tags_yaml = "\n".join(f"  - {t}" for t in tags)
    source_title = _yaml_str(result.get("source_title", ""))
    authors = _yaml_str(result.get("authors", ""))
    # shared_by kept as internal metadata only (not displayed in the UI)
    shared_by_line = f'\nshared_by: "{_yaml_str(shared_by)}"' if shared_by else ""
    source_title_line = f'\nsource_title: "{source_title}"' if source_title else ""
    authors_line = f'\nauthors: "{authors}"' if authors else ""

    frontmatter = f"""\
---
title: "{result['title']}"
description: "{result['description']}"
category: "{result['category']}"
date: "{today}"
type: "topic"
source_url: "{url}"{source_title_line}{authors_line}{shared_by_line}
tags:
{tags_yaml}
featured: false
---"""

    body = result.get("mdx_content", "").strip()
    return f"{frontmatter}\n\n{body}\n"


def is_duplicate(
    candidate_url: str,
    candidate_slug: str,
    existing_articles: list[dict],
    articles_dir: Path,
) -> bool:
    """Return True if this article is already covered."""
    # Slug collision
    if (articles_dir / f"{candidate_slug}.mdx").exists():
        return True
    # source_url collision
    if any(a.get("source_url") == candidate_url for a in existing_articles):
        return True
    return False


def open_pr(project_root: Path, generated: list[dict], today: str) -> None:
    """Create a branch, commit generated files, and open a PR."""
    branch = f"articles/auto-{today}"

    def run(*args: str) -> None:
        result = subprocess.run(
            list(args), cwd=project_root, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  Command failed: {' '.join(args)}")
            print(f"  stderr: {result.stderr.strip()}")
            raise RuntimeError(f"git command failed: {' '.join(args)}")

    # Create and switch to branch
    run("git", "checkout", "-b", branch)

    # Stage generated files
    for item in generated:
        run("git", "add", item["path"])

    # Commit
    run(
        "git",
        "commit",
        "-m",
        f"Auto-generate topic articles {today}",
    )

    # Push
    run("git", "push", "origin", branch)

    # Build PR body
    article_lines = "\n".join(
        f"- **{item['title']}** — {item['url']}" for item in generated
    )
    pr_body = f"""\
## Auto-generated topic articles ({today})

These articles were generated from links shared by monitored Twitter/X accounts.
Please review each article for accuracy, tone, and fit before merging.

### Generated articles

{article_lines}

---
*Generated by `scripts/generate-articles.py`*
"""

    subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            f"Auto-generated articles ({today})",
            "--body",
            pr_body,
        ],
        cwd=project_root,
        check=True,
    )

    print(f"\nPR opened for branch {branch}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        raise SystemExit(1)

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    articles_dir = project_root / ARTICLES_DIR_RELATIVE
    articles_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    client = anthropic.Anthropic()

    # Load data
    all_news = load_news_items(project_root)
    candidates = twitter_candidates(all_news)
    print(f"Twitter candidates in news.json: {len(candidates)}")

    if not candidates:
        print("No Twitter items found — nothing to generate.")
        return

    existing_articles = load_existing_articles(articles_dir)
    print(f"Existing articles: {len(existing_articles)}")

    generated: list[dict] = []

    for item in candidates:
        url = item.get("url", "")
        source = item.get("source", "")
        print(f"\nEvaluating: {url}")
        print(f"  Shared by: {source}")

        # Preliminary duplicate guard before any API call
        # We don't know the slug yet, so just check source_url
        if any(a.get("source_url") == url for a in existing_articles):
            print("  Skipping — source_url already exists in articles.")
            continue

        # Fetch full content
        article_text = fetch_full_article(url)
        if not article_text:
            print("  Skipping — could not fetch article content.")
            continue

        # Evaluate + generate
        print("  Calling Claude...")
        try:
            result = evaluate_and_generate(client, url, article_text, existing_articles)
        except anthropic.APIError as e:
            print(f"  API error: {e}")
            continue

        if not result:
            print("  Skipping — could not parse Claude response.")
            continue

        if not result.get("worthy"):
            print(f"  Not worthy: {result.get('reason', 'no reason given')}")
            continue

        slug = result.get("slug", "")
        if not slug:
            print("  Skipping — no slug in response.")
            continue

        print(f"  Worthy! Slug: {slug}")
        print(f"  Reason: {result.get('reason', '')}")

        # Full duplicate guard now we have the slug
        if is_duplicate(url, slug, existing_articles, articles_dir):
            print("  Skipping — duplicate detected.")
            continue

        # Assemble and save
        mdx = assemble_mdx(result, url, today, shared_by=source)
        output_path = articles_dir / f"{slug}.mdx"
        output_path.write_text(mdx)
        print(f"  Saved: {output_path.relative_to(project_root)}")

        generated.append(
            {
                "slug": slug,
                "title": result.get("title", slug),
                "url": url,
                "path": str(output_path.relative_to(project_root)),
            }
        )

        # Update in-memory list so subsequent iterations see the new article
        existing_articles.append(
            {"slug": slug, "title": result.get("title", slug), "source_url": url}
        )

    print(f"\nGenerated {len(generated)} article(s).")

    if not generated:
        print("Nothing to commit.")
        return

    # Only open PR in CI (when GITHUB_TOKEN is present)
    if os.environ.get("GITHUB_TOKEN"):
        print("Opening PR...")
        try:
            open_pr(project_root, generated, today)
        except Exception as e:
            print(f"WARNING: Could not open PR: {e}")
            print("Generated files are saved; you can open a PR manually.")
    else:
        print("GITHUB_TOKEN not set — skipping PR creation.")
        print("Generated files:")
        for item in generated:
            print(f"  {item['path']}")


if __name__ == "__main__":
    main()
