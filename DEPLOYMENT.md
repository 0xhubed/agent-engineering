# Deployment Guide

## Deploy to Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **Import Git Repository**
3. Select the `agent-engineering` repo
4. Vercel auto-detects Astro - click **Deploy**
5. Wait ~1 minute for build to complete

Your site will be live at `https://agent-engineering.vercel.app` (or your custom domain).

## Automated News Updates

The GitHub Actions workflow runs daily at **8:00 AM UTC** to fetch and process AI agent news.

### How it works

1. Fetches RSS feeds from LangChain, Anthropic, OpenAI, Google AI, Hugging Face
2. Uses Claude to filter and summarize relevant agent engineering news
3. Commits updated `src/data/news.json` to the repo
4. Vercel detects the commit and auto-redeploys

### Required Secret

The `ANTHROPIC_API_KEY` must be added to GitHub repository secrets:

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your Anthropic API key

### Manual Trigger

To run the news update manually:

1. Go to your GitHub repo → **Actions** tab
2. Click **"Update News"** workflow on the left
3. Click **"Run workflow"** → **"Run workflow"**

### Modify Schedule

Edit `.github/workflows/update-news.yml` to change the schedule:

```yaml
on:
  schedule:
    - cron: '0 8 * * *'  # 8:00 AM UTC daily
```

Common schedules:
- `'0 8 * * *'` - Daily at 8am UTC
- `'0 */12 * * *'` - Every 12 hours
- `'0 8 * * 1'` - Weekly on Monday at 8am UTC

### Add/Remove News Sources

Edit `scripts/update-news.py` and modify the `FEEDS` list:

```python
FEEDS = [
    {
        "name": "Source Name",
        "url": "https://example.com/rss.xml",
        "category": "frameworks",  # or: providers, tools
    },
    # ...
]
```

## Enable Vercel Analytics

1. Go to your Vercel project dashboard
2. Click **Analytics** tab
3. Click **Enable**

Analytics will show page views, Web Vitals, and visitor insights.

## Custom Domain (Optional)

1. Go to Vercel project → **Settings** → **Domains**
2. Add your domain
3. Update DNS records as instructed by Vercel
