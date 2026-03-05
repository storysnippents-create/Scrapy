# Scrapy + FastAPI Scraping Service

A production-safe web scraping API that runs Scrapy spiders via subprocess, triggered over HTTP. Designed for **Windows + Python 3.10+** and **n8n** integration.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Test — Health Check

```bash
curl http://localhost:8000/
```

Expected response:

```json
{"status": "ok"}
```

### 4. Test — Scrape

```bash
curl -X POST http://localhost:8000/scrape ^
  -H "Content-Type: application/json" ^
  -d "{\"urls\": [\"https://example.com\"]}"
```

Expected response:

```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "url": "https://example.com/",
      "title": "Example Domain",
      "description": "",
      "emails": [],
      "social_links": {},
      "text": "Example Domain This domain is for use in illustrative examples..."
    }
  ]
}
```

---

## n8n Integration

1. Add an **HTTP Request** node in your n8n workflow.
2. Configure:

| Setting       | Value                                  |
|---------------|----------------------------------------|
| Method        | `POST`                                 |
| URL           | `http://<your-server-ip>:8000/scrape`  |
| Body Type     | JSON                                   |
| JSON Body     | `{ "urls": ["https://example.com"] }`  |

3. The node will receive a JSON array of scraped data in `data`.

---

## Architecture

```
n8n / curl
    │
    ▼   HTTP POST /scrape
┌───────────┐
│  FastAPI   │   (api/app.py)
│  Controller│   — writes urls.txt
│            │   — runs `scrapy crawl` via subprocess
│            │   — reads items.jsonl
│            │   — returns JSON
└───────────┘
    │  subprocess.run(...)
    ▼
┌───────────┐
│  Scrapy   │   (scraper/)
│  Spider   │   — reads urls.txt
│            │   — crawls pages
│            │   — writes items.jsonl
└───────────┘
```

**Key design rule:** Scrapy NEVER runs inside the FastAPI event loop. It is always a separate OS process.

---

## Project Structure

```
project-root/
├── api/
│   └── app.py                # FastAPI controller ONLY
├── scraper/
│   ├── scrapy.cfg
│   └── scraper/
│       ├── __init__.py
│       ├── settings.py
│       ├── pipelines.py
│       └── spiders/
│           ├── __init__.py
│           └── business_spider.py
├── requirements.txt
└── README.md
```

## Configuration

Edit `scraper/scraper/settings.py` to change:

| Setting              | Default | Description              |
|----------------------|---------|--------------------------|
| `DOWNLOAD_DELAY`     | `1`     | Seconds between requests |
| `ROBOTSTXT_OBEY`     | `True`  | Respect robots.txt       |
| `CONCURRENT_REQUESTS`| `8`     | Max parallel requests    |
