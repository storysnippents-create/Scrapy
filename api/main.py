from fastapi import FastAPI
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraper.scraper.spiders.your_spider import YourSpider

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Scrapy API running"}

@app.get("/scrape")
def run_spider(query: str = "test"):

    process = CrawlerProcess(get_project_settings())

    results = []

    class CustomSpider(YourSpider):
        def parse(self, response):
            for item in super().parse(response):
                results.append(item)
                yield item

    process.crawl(CustomSpider, query=query)
    process.start()

    return results