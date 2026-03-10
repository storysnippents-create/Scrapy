import os
import sys

# Set up the paths before any scraper imports
# This ensures that "import scraper" resolves to the inner scraper package
sys.path.insert(0, os.path.abspath("scraper"))
os.chdir("scraper")

from fastapi import FastAPI
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraper.spiders.business_spider import BusinessSpider


app = FastAPI()

@app.get("/")
def home():
    return {"status": "Scrapy API running"}


@app.get("/scrape")
def run_spider(url: str):

    process = CrawlerProcess(get_project_settings())

    results = []

    class CustomSpider(BusinessSpider):

        def parse(self, response):
            for item in super().parse(response):
                results.append(item)
                yield item

    process.crawl(CustomSpider, url=url)
    process.start()

    return {"results": results}