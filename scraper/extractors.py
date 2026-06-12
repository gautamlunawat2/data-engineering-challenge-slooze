"""
HTML extraction logic for IndiaMART search-results pages.

IndiaMART uses server-rendered HTML; product cards live inside
<div class="prd-list"> containers. This module handles the DOM
parsing and normalises the output into plain dicts.
"""
from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

from .utils import clean_text, parse_price_range


# ── helpers ────────────────────────────────────────────────────────────────────

def _text(tag: Optional[Tag], selector: str, attr: Optional[str] = None) -> Optional[str]:
    """Safe single-element text/attr getter."""
    if tag is None:
        return None
    el = tag.select_one(selector)
    if el is None:
        return None
    if attr:
        return clean_text(el.get(attr))
    return clean_text(el.get_text(separator=" ", strip=True))


def _all_text(tag: Optional[Tag], selector: str) -> list[str]:
    if tag is None:
        return []
    return [clean_text(el.get_text(strip=True)) for el in tag.select(selector) if el.get_text(strip=True)]


# ── main extractor ─────────────────────────────────────────────────────────────

def extract_products(html: str, category: str) -> list[dict]:
    """
    Parse the raw HTML of an IndiaMART search-results page and return a
    list of product dicts.  Handles multiple card layouts that IndiaMART
    uses across different categories.
    """
    soup = BeautifulSoup(html, "lxml")
    products: list[dict] = []

    # IndiaMART renders product cards with several possible container classes
    card_selectors = [
        "div.prd-list",          # standard listing
        "div.product-unit",      # alternate layout
        "div.result-content",    # search results
        "li.lst-cont-wrap",      # list view
        "div.bx",                # category pages
    ]

    cards: list[Tag] = []
    for sel in card_selectors:
        found = soup.select(sel)
        if found:
            cards.extend(found)
            break

    # Fallback: any div containing both a price and a title-like link
    if not cards:
        cards = _fallback_cards(soup)

    for card in cards:
        product = _parse_card(card, category)
        if product and product.get("product_name"):
            products.append(product)

    return products


def _fallback_cards(soup: BeautifulSoup) -> list[Tag]:
    """
    Last-resort heuristic: collect divs that look like product cards
    by checking for co-presence of a link and a price-like string.
    """
    candidates = []
    for div in soup.find_all("div"):
        text = div.get_text()
        if re.search(r"₹\s*[\d,]+", text) and div.find("a"):
            # avoid huge containers that wrap the entire page
            if len(div.get_text()) < 2000:
                candidates.append(div)
    return candidates[:50]


def _parse_card(card: Tag, category: str) -> dict:
    # ── product name ────────────────────────────────────────────────────────
    name = (
        _text(card, "div.prd-name a")
        or _text(card, "h3.prd-name a")
        or _text(card, "a.prd-name")
        or _text(card, "div.prod-name a")
        or _text(card, "h2 a")
        or _text(card, "h3 a")
        or _text(card, "a[title]", attr="title")
    )

    # ── price ────────────────────────────────────────────────────────────────
    raw_price = (
        _text(card, "div.prc")
        or _text(card, "span.prc")
        or _text(card, "div.price-unit")
        or _text(card, "span.price")
    )
    min_price, max_price = parse_price_range(raw_price)

    # ── unit ─────────────────────────────────────────────────────────────────
    unit = _text(card, "div.uom") or _text(card, "span.uom")

    # ── supplier ─────────────────────────────────────────────────────────────
    supplier = (
        _text(card, "div.lcname a")
        or _text(card, "span.comp-name a")
        or _text(card, "div.company-name a")
        or _text(card, "p.cmp-name a")
    )

    # ── location ─────────────────────────────────────────────────────────────
    location = (
        _text(card, "span.lcnm")
        or _text(card, "div.loc")
        or _text(card, "span.city-name")
        or _text(card, "p.lcnm")
    )

    # ── verified / trusted supplier badge ────────────────────────────────────
    verified = bool(
        card.select_one("span.verified")
        or card.select_one("img[alt*='Verified']")
        or card.select_one("div.trust-badge")
    )

    # ── star rating ──────────────────────────────────────────────────────────
    rating_tag = card.select_one("span.starRate") or card.select_one("div.rating span")
    rating: Optional[float] = None
    if rating_tag:
        try:
            rating = float(rating_tag.get_text(strip=True))
        except ValueError:
            pass

    # ── review count ─────────────────────────────────────────────────────────
    review_tag = card.select_one("span.cnt") or card.select_one("span.review-count")
    reviews: Optional[int] = None
    if review_tag:
        m = re.search(r"\d+", review_tag.get_text())
        if m:
            reviews = int(m.group())

    # ── product URL ──────────────────────────────────────────────────────────
    link_tag = card.select_one("div.prd-name a") or card.select_one("a[href*='proddetail']")
    url = link_tag["href"] if link_tag and link_tag.get("href") else None

    # ── description snippet ───────────────────────────────────────────────────
    desc = (
        _text(card, "div.prd-desc")
        or _text(card, "p.description")
        or _text(card, "div.product-desc")
    )

    # ── minimum order quantity ───────────────────────────────────────────────
    moq = _text(card, "div.moq") or _text(card, "span.moq")

    return {
        "product_name":   name,
        "category":       category,
        "min_price_inr":  min_price,
        "max_price_inr":  max_price,
        "price_unit":     unit,
        "raw_price":      raw_price,
        "supplier_name":  supplier,
        "location":       location,
        "verified":       verified,
        "rating":         rating,
        "review_count":   reviews,
        "min_order_qty":  moq,
        "description":    desc,
        "product_url":    url,
    }
