"""
FastAPI controller for the Scrapy scraping service.

⚠  Zero Scrapy imports here — Scrapy is executed ONLY via subprocess.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

# Windows: prevent CTRL+C from propagating to child subprocess
IS_WINDOWS = sys.platform == "win32"

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Scrapy Scraping Service",
    description="Trigger Scrapy spiders via HTTP. Designed for n8n integration.",
    version="1.0.0",
)

# Paths
SCRAPER_DIR = Path(__file__).resolve().parent.parent / "scraper"
URLS_FILE = SCRAPER_DIR / "urls.txt"
ITEMS_FILE = SCRAPER_DIR / "items.jsonl"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ScrapeRequest(BaseModel):
    urls: List[HttpUrl]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _cleanup():
    """Remove temporary files produced by a scrape run."""
    for f in (URLS_FILE, ITEMS_FILE):
        try:
            f.unlink(missing_ok=True)
        except OSError:
            pass


def _run_scrapy(urls: List[str]) -> list:
    """
    Write URLs to disk, invoke Scrapy via subprocess, read output, clean up.
    Returns a list of dicts (one per page crawled).
    """
    # 1. Write URLs
    URLS_FILE.write_text("\n".join(urls), encoding="utf-8")

    # 2. Remove stale output
    if ITEMS_FILE.exists():
        ITEMS_FILE.unlink()

    # 3. Run Scrapy as a completely separate process
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "business_spider",
        "-a", f"urls_file={URLS_FILE}",
        "-o", str(ITEMS_FILE),
        "--nolog",                       # suppress logs in subprocess stdout
        "-s", "LOG_FILE=scrapy.log",     # log to file instead
    ]

    # Build platform-specific kwargs for subprocess
    kwargs = dict(
        cwd=str(SCRAPER_DIR),
        capture_output=True,
        text=True,
        timeout=300,            # 5-minute safety net
    )

    if IS_WINDOWS:
        # CREATE_NEW_PROCESS_GROUP prevents CTRL+C from propagating to child
        # CREATE_NO_WINDOW prevents a console window from flashing
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )

    result = subprocess.run(cmd, **kwargs)

    if result.returncode != 0:
        error_detail = result.stderr or result.stdout or "Unknown Scrapy error"
        raise RuntimeError(f"Scrapy exited with code {result.returncode}: {error_detail}")

    # 4. Parse JSONL output
    items = []
    if ITEMS_FILE.exists():
        for line in ITEMS_FILE.read_text(encoding="utf-8").strip().splitlines():
            line = line.strip()
            if line:
                items.append(json.loads(line))

    return items


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def health_check():
    return {"status": "ok"}


@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    if not request.urls:
        raise HTTPException(status_code=400, detail="urls list must not be empty")

    url_strings = [str(u) for u in request.urls]

    try:
        # Run the blocking subprocess in a thread so the event loop stays free
        items = await asyncio.to_thread(_run_scrapy, url_strings)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Scrapy timed out after 300 seconds")
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")
    finally:
        _cleanup()

    return {
        "status": "success",
        "count": len(items),
        "data": items,
    }
