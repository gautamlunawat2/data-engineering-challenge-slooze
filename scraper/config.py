"""
Centralised configuration for the IndiaMART scraper.
All tuneable knobs live here so callers never hard-code values.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class ScraperConfig:
    # ── target categories ──────────────────────────────────────────────────
    categories: List[dict] = field(default_factory=lambda: [
        {"name": "Industrial Machinery",  "query": "industrial+machinery"},
        {"name": "Electronics",           "query": "electronics+components"},
        {"name": "Textiles & Apparel",    "query": "textiles+fabric"},
        {"name": "Chemical & Pharma",     "query": "chemical+raw+material"},
        {"name": "Agricultural Products", "query": "agricultural+products"},
    ])

    # ── pagination ─────────────────────────────────────────────────────────
    max_pages_per_category: int = 5   # IndiaMART paginates in 20-item pages
    items_per_page: int = 20

    # ── rate limiting ──────────────────────────────────────────────────────
    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 5.0
    request_timeout: int = 15

    # ── retry policy ──────────────────────────────────────────────────────
    max_retries: int = 3
    retry_wait_min: int = 4
    retry_wait_max: int = 10

    # ── output ────────────────────────────────────────────────────────────
    output_dir: str = "data/raw"
    processed_dir: str = "data/processed"

    # ── HTTP headers ──────────────────────────────────────────────────────
    base_headers: dict = field(default_factory=lambda: {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    })

    # ── IndiaMART endpoints ────────────────────────────────────────────────
    search_url: str = "https://dir.indiamart.com/search.mp"
    base_url: str = "https://www.indiamart.com"
