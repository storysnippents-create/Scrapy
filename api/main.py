import os
import sys
import json
import uuid
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

class ScrapeRequest(BaseModel):
    url: str

app = FastAPI()

# Absolute path to the scraper project directory where scrapy.cfg lives
SCRAPER_DIR = os.path.abspath("scraper")

@app.get("/")
def home():
    return {"status": "Scrapy API running (Production Mode)"}

def execute_spider(target_url: str):
    if not target_url:
        raise HTTPException(status_code=400, detail="Missing 'url' parameter")

    # Generate a unique temp file name for this specific request
    filename = f"temp_{uuid.uuid4().hex}.json"
    filepath = os.path.join(SCRAPER_DIR, filename)

    try:
        # Run Scrapy in a new process to avoid Twisted reactor errors
        command = [
            sys.executable, "-m", "scrapy", "crawl", "business_spider",
            "-a", f"url={target_url}",
            "-o", filename
        ]

        result = subprocess.run(
            command,
            cwd=SCRAPER_DIR,
            capture_output=True,
            text=True
        )

        # Catch obvious failure codes from Scrapy
        if result.returncode != 0:
            raise HTTPException(
                status_code=500, 
                detail=f"Scrapy execution failed: {result.stderr or result.stdout}"
            )

        # Load the scraped data if the file was produced
        if not os.path.exists(filepath):
            return {"results": []}

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {"results": data}

    except HTTPException as he:
        # Re-raise FastAPIs internal exceptions
        raise he
    except Exception as e:
        # Catch unexpected errors (e.g. JSON decode error)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up the file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass


@app.get("/scrape")
def run_spider_get(url: str):
    return execute_spider(url)

@app.post("/scrape")
def run_spider_post(url: Optional[str] = None, payload: Optional[ScrapeRequest] = None):
    target_url = url or (payload.url if payload else None)
    return execute_spider(target_url)
