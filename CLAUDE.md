# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Engineering is a static documentation site about AI agent patterns, built with Astro and Tailwind CSS. It covers topics like tool use, ReAct pattern, memory systems, multi-agent orchestration, MCP/A2A protocols, and evaluation.

## Commands

```bash
npm run dev      # Start dev server (localhost:4321)
npm run build    # Type-check and build for production
npm run preview  # Preview production build
```

## Architecture

### Site Structure
- Base path: `/agent-engineering` (configured in `astro.config.mjs`)
- Output: Static site generation
- Styling: Tailwind CSS with dark mode support (class-based)

### Page Organization
```
src/pages/
├── index.astro              # Homepage
├── topics/
│   ├── index.astro          # Topics listing (defines topic metadata)
│   └── [topic]/index.astro  # Individual topic pages
├── benchmarks/index.astro   # Benchmarks page
└── resources/index.astro    # Curated resources (papers, frameworks, tools)
```

### Components
- `BaseLayout.astro` - Main layout with header, nav, footer, dark mode toggle
- `CodeBlock.astro` - Tabbed code blocks with language switching and copy button
- `Callout.astro` - Info/warning/tip callouts
- `Table.astro` - Styled data tables
- `Diagram.astro` - ASCII/text diagrams

### Code Example Pattern
Topic pages define code examples as arrays of objects with `language`, `label`, and `code` properties, then pass them to `<CodeBlock tabs={...} />`:

```javascript
const example = [
  { language: 'pseudo', label: 'Pseudo-code', code: `...` },
  { language: 'python', label: 'Python (LangChain)', code: `...` },
  { language: 'csharp', label: 'C# (Agent Framework)', code: `...` },
];
```

### Framework Standards for Code Samples
- **Python**: Use LangChain/LangGraph (not raw OpenAI/Anthropic clients)
- **C#**: Use Microsoft Agent Framework (not AutoGen or Semantic Kernel directly)
- Exception: `prompt-caching` shows native provider APIs for provider-specific caching features

### Adding New Topics
1. Add entry to `topics` array in `src/pages/topics/index.astro`
2. Create `src/pages/topics/[topic-slug]/index.astro`
3. Import components: `BaseLayout`, `CodeBlock`, `Callout`, `Table`, `Diagram`
4. Follow existing topic structure: header, sections with h2/h3, code examples, callouts

## Automated News Updates

A GitHub Actions workflow (`update-news.yml`) runs daily to fetch AI agent news:

1. **Fetches RSS feeds** from LangChain, Anthropic, OpenAI, Google AI, Hugging Face
2. **Filters with Claude** to select relevant agent engineering news
3. **Updates `src/data/news.json`** with processed items
4. **Auto-commits** changes, triggering site rebuild

### Manual Trigger
Run workflow manually from GitHub Actions tab or:
```bash
python scripts/update-news.py  # Requires ANTHROPIC_API_KEY env var
```

### Configuration
- **Feeds**: Edit `FEEDS` list in `scripts/update-news.py`
- **Schedule**: Edit cron in `.github/workflows/update-news.yml` (default: 8am UTC daily)
- **Secret**: Requires `ANTHROPIC_API_KEY` in GitHub repository secrets
