"""
Utility helpers: user-agent rotation, rate limiting, logging setup.
"""
import logging
import random
import time
from typing import Optional


# ── Logging ──────────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
            datefmt="%H:%M:%S",
        ))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


# ── User-agent pool ───────────────────────────────────────────────────────────

_USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]


def random_user_agent() -> str:
    return random.choice(_USER_AGENTS)


# ── Rate limiting ─────────────────────────────────────────────────────────────

def polite_sleep(min_s: float = 2.0, max_s: float = 5.0) -> None:
    """Sleep for a random duration to avoid hammering the server."""
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)


# ── Price parsing ─────────────────────────────────────────────────────────────

def parse_price(raw: Optional[str]) -> Optional[float]:
    """
    Convert a raw price string like '₹1,200 - ₹3,500/Piece' to a float
    representing the lower bound in INR. Returns None if unparseable.
    """
    if not raw:
        return None
    import re
    cleaned = re.sub(r"[₹$,\s]", "", raw.split("-")[0].split("/")[0])
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_price_range(raw: Optional[str]) -> tuple[Optional[float], Optional[float]]:
    """Return (min_price, max_price) tuple from a range string."""
    if not raw:
        return None, None
    import re
    parts = raw.split("-")
    prices = []
    for p in parts:
        cleaned = re.sub(r"[₹$,\s]", "", p.split("/")[0])
        try:
            prices.append(float(cleaned))
        except ValueError:
            prices.append(None)
    if len(prices) == 1:
        return prices[0], prices[0]
    return prices[0], prices[1] if len(prices) > 1 else (None, None)


# ── Text cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    return " ".join(text.split())
