import re
from pathlib import Path
from urllib.parse import urlparse

import scrapy


class BusinessSpider(scrapy.Spider):
    """
    General-purpose business info spider.

    Usage:
        scrapy crawl business_spider -a urls_file=urls.txt -o items.jsonl
    """

    name = "business_spider"

    # Regex for email extraction
    EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

    # Social platform patterns  →  (platform_key, compiled regex)
    SOCIAL_PATTERNS = [
        ("facebook",  re.compile(r"https?://(?:www\.)?facebook\.com/[^\s\"'<>]+")),
        ("twitter",   re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/[^\s\"'<>]+")),
        ("linkedin",  re.compile(r"https?://(?:www\.)?linkedin\.com/[^\s\"'<>]+")),
        ("instagram", re.compile(r"https?://(?:www\.)?instagram\.com/[^\s\"'<>]+")),
        ("youtube",   re.compile(r"https?://(?:www\.)?youtube\.com/[^\s\"'<>]+")),
        ("github",    re.compile(r"https?://(?:www\.)?github\.com/[^\s\"'<>]+")),
        ("tiktok",    re.compile(r"https?://(?:www\.)?tiktok\.com/[^\s\"'<>]+")),
        ("pinterest", re.compile(r"https?://(?:www\.)?pinterest\.com/[^\s\"'<>]+")),
    ]

    def __init__(self, urls_file: str = "urls.txt", *args, **kwargs):
        super().__init__(*args, **kwargs)
        urls_path = Path(urls_file)
        if not urls_path.is_absolute():
            # Resolve relative to the scraper project root (where scrapy.cfg lives)
            urls_path = Path(__file__).resolve().parents[2] / urls_file

        self.logger.info("Loading URLs from %s", urls_path)
        raw_urls = urls_path.read_text(encoding="utf-8").strip().splitlines()
        self.start_urls = [u.strip() for u in raw_urls if u.strip()]

        # Restrict crawling to only the provided domains
        self.allowed_domains = list(
            {urlparse(u).netloc for u in self.start_urls if urlparse(u).netloc}
        )
        self.logger.info("Allowed domains: %s", self.allowed_domains)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    def parse(self, response):
        page_url = response.url
        title = response.css("title::text").get(default="").strip()
        description = (
            response.xpath('//meta[@name="description"]/@content').get(default="").strip()
        )

        # Visible text — strip scripts/styles, collapse whitespace
        body_text = self._extract_visible_text(response)

        # Emails
        emails = list(set(self.EMAIL_RE.findall(response.text)))

        # Social links
        social_links = self._extract_social_links(response.text)

        yield {
            "url": page_url,
            "title": title,
            "description": description,
            "emails": emails,
            "social_links": social_links,
            "text": body_text,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_visible_text(response) -> str:
        """Return cleaned visible text from the page body."""
        # Remove <script> and <style> content first
        sel = response.xpath(
            "//body//*[not(self::script or self::style or self::noscript)]//text()"
        )
        raw_parts = sel.getall()
        text = " ".join(part.strip() for part in raw_parts if part.strip())
        # Collapse multiple spaces
        return re.sub(r"\s{2,}", " ", text).strip()

    def _extract_social_links(self, html: str) -> dict:
        """Scan raw HTML for social media URLs and return a dict keyed by platform."""
        result = {}
        for platform, pattern in self.SOCIAL_PATTERNS:
            matches = list(set(pattern.findall(html)))
            if matches:
                result[platform] = matches if len(matches) > 1 else matches[0]
        return result
