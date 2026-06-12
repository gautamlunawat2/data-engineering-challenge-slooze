"""
Persistence helpers: load raw JSON files, save processed CSV/JSON,
and provide a simple merge-and-deduplicate function.
"""
from __future__ import annotations

import json
import os
from glob import glob
from typing import Optional

import pandas as pd

from .utils import get_logger

logger = get_logger(__name__)


def load_raw_json(directory: str = "data/raw") -> list[dict]:
    """Load and concatenate all JSON files from *directory*."""
    files = sorted(glob(os.path.join(directory, "*.json")))
    if not files:
        logger.warning("No raw JSON files found in %s", directory)
        return []

    all_records: list[dict] = []
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Loaded %d records from %s", len(data), fp)
        all_records.extend(data)

    return all_records


def to_dataframe(records: list[dict]) -> pd.DataFrame:
    """Convert a list of product dicts to a cleaned DataFrame."""
    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Normalise column types
    for col in ("min_price_inr", "max_price_inr", "rating"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "review_count" in df.columns:
        df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce").astype("Int64")

    if "verified" in df.columns:
        df["verified"] = df["verified"].fillna(False).astype(bool)

    if "scraped_at" not in df.columns:
        from datetime import datetime
        df["scraped_at"] = datetime.utcnow().isoformat()

    # Drop complete duplicates
    df = df.drop_duplicates(subset=["product_name", "supplier_name", "min_price_inr"],
                             keep="first")
    df = df.reset_index(drop=True)
    return df


def save_processed(df: pd.DataFrame, directory: str = "data/processed",
                   stem: Optional[str] = None) -> dict[str, str]:
    """Save DataFrame as both CSV and JSON; returns paths dict."""
    os.makedirs(directory, exist_ok=True)
    if stem is None:
        from datetime import datetime
        stem = f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    csv_path  = os.path.join(directory, f"{stem}.csv")
    json_path = os.path.join(directory, f"{stem}.json")

    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_json(json_path, orient="records", indent=2, force_ascii=False)

    logger.info("Saved processed data → %s  |  %s", csv_path, json_path)
    return {"csv": csv_path, "json": json_path}
