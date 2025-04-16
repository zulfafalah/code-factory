# scrapers.py
from .base_scraper import BaseScraper
from .scraper_registry import register_scraper_class


@register_scraper_class("Tokopedia")
class TokopediaScraper(BaseScraper):
    def run(self):
        print(f"[TOKOPEDIA] Scraping order {self.order.order_id}")
        # your scraping logic here


@register_scraper_class("Review Shopee")
class ShopeeScraper(BaseScraper):
    def run(self):
        print(f"[SHOPEE] Scraping order {self.order.order_id}")
        return f"[SHOPEE] Scraping order {self.order.order_id}"
        # your scraping logic here
