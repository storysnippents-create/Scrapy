# Scrapy settings for scraper project

BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# --- Polite crawling defaults ---
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DEPTH_LIMIT = 1
DOWNLOAD_DELAY = 1
CLOSESPIDER_PAGECOUNT = 5

# --- Disable features that conflict with subprocess usage ---
TELNETCONSOLE_ENABLED = False

# Prevent Scrapy from installing its own signal handlers.
# Critical for running via subprocess spawned from FastAPI.
LOG_ENABLED = True
LOG_LEVEL = "ERROR"

# --- Request headers ---
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en",
}

# --- Item pipelines ---
ITEM_PIPELINES = {
    "scraper.pipelines.CleanTextPipeline": 300,
}

# --- Feed export ---
FEED_EXPORT_ENCODING = "utf-8"

# --- Misc ---
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
