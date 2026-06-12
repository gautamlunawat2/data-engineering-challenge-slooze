"""
IndiaMART crawler.

Orchestrates HTTP requests, pagination, retry logic, and hands off
raw HTML to extractors.  Falls back to synthetic data generation when
the live site is inaccessible (rate-limited, blocked, or offline) so
the EDA pipeline always has data to work with.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_random, retry_if_exception_type

from .config import ScraperConfig
from .extractors import extract_products
from .mock_data import generate_mock_dataset
from .utils import get_logger, polite_sleep, random_user_agent

logger = get_logger(__name__)


class IndiaMArtCrawler:
    """
    Crawls IndiaMART search-result pages for a list of product categories.

    Usage
    -----
    crawler = IndiaMArtCrawler()
    results = crawler.run()          # scrapes live site
    results = crawler.run(mock=True) # uses synthetic data
    """

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.cfg = config or ScraperConfig()
        self.session = self._build_session()
        self._scraped_count = 0

    # ── public API ─────────────────────────────────────────────────────────────

    def run(self, mock: bool = False) -> list[dict]:
        """
        Main entry point.  Returns a flat list of product dicts.
        If mock=True (or live scraping yields 0 products after the first
        category), falls back to synthetic data.
        """
        if mock:
            logger.info("Mock mode: generating synthetic dataset")
            return self._save_and_return(generate_mock_dataset())

        all_products: list[dict] = []
        consecutive_empty = 0

        for cat in self.cfg.categories:
            logger.info("Scraping category: %s", cat["name"])
            products = self._scrape_category(cat)
            logger.info("  → %d products collected", len(products))
            all_products.extend(products)

            if len(products) == 0:
                consecutive_empty += 1
            else:
                consecutive_empty = 0

            # If the first two categories return nothing, the site is
            # blocking us → switch to synthetic data automatically.
            if consecutive_empty >= 2 and len(all_products) == 0:
                logger.warning("Site appears to be blocking requests. Switching to mock data.")
                return self._save_and_return(generate_mock_dataset())

            polite_sleep(self.cfg.min_delay_seconds, self.cfg.max_delay_seconds)

        if not all_products:
            logger.warning("No products scraped. Using mock data as fallback.")
            return self._save_and_return(generate_mock_dataset())

        return self._save_and_return(all_products)

    # ── internals ──────────────────────────────────────────────────────────────

    def _scrape_category(self, category: dict) -> list[dict]:
        products: list[dict] = []
        for page in range(1, self.cfg.max_pages_per_category + 1):
            url = self._build_url(category["query"], page)
            logger.info("  Page %d: %s", page, url)
            html = self._fetch(url)
            if html is None:
                logger.warning("  Skipping page %d (fetch failed)", page)
                break

            page_products = extract_products(html, category["name"])
            if not page_products:
                logger.info("  No products on page %d, stopping pagination", page)
                break

            products.extend(page_products)
            polite_sleep(self.cfg.min_delay_seconds, self.cfg.max_delay_seconds)

        return products

    def _build_url(self, query: str, page: int) -> str:
        offset = (page - 1) * self.cfg.items_per_page
        return (
            f"{self.cfg.search_url}"
            f"?ss={query}"
            f"&prdsrc=1"
            f"&imcat=0"
            f"&biz=0"
            f"&offset={offset}"
            f"&limit={self.cfg.items_per_page}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random(min=4, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=False,
    )
    def _fetch(self, url: str) -> Optional[str]:
        try:
            self.session.headers.update({"User-Agent": random_user_agent()})
            resp = self.session.get(url, timeout=self.cfg.request_timeout)
            if resp.status_code == 200:
                return resp.text
            if resp.status_code in (429, 503):
                logger.warning("Rate limited (%s). Waiting 30 s…", resp.status_code)
                time.sleep(30)
                return None
            logger.warning("HTTP %s for %s", resp.status_code, url)
            return None
        except requests.RequestException as exc:
            logger.error("Request error: %s", exc)
            raise

    def _build_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update(self.cfg.base_headers)
        s.headers["Referer"] = self.cfg.base_url
        return s

    def _save_and_return(self, products: list[dict]) -> list[dict]:
        os.makedirs(self.cfg.output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.cfg.output_dir, f"products_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        logger.info("Saved %d products → %s", len(products), path)
        return products
