"""
Exploratory Data Analysis engine.

All analysis is encapsulated in EDAAnalyzer so it can be used from
main.py, the Jupyter notebook, or unit tests without side effects.
"""
from __future__ import annotations

import os
import textwrap
from typing import Optional

import numpy as np
import pandas as pd

from scraper.utils import get_logger

logger = get_logger(__name__)


class EDAAnalyzer:
    """
    Accepts a cleaned DataFrame (output of storage.to_dataframe) and
    exposes methods to generate summary statistics and insights.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._enrich()

    # ── data enrichment ───────────────────────────────────────────────────────

    def _enrich(self) -> None:
        """Derive helper columns used across multiple analyses."""
        df = self.df
        # mid-price for price analysis
        if "min_price_inr" in df.columns and "max_price_inr" in df.columns:
            df["mid_price_inr"] = (
                df["min_price_inr"].fillna(df["max_price_inr"])
                + df["max_price_inr"].fillna(df["min_price_inr"])
            ) / 2

        # price spread
        if "min_price_inr" in df.columns and "max_price_inr" in df.columns:
            df["price_spread_pct"] = (
                (df["max_price_inr"] - df["min_price_inr"])
                / df["min_price_inr"].replace(0, np.nan)
                * 100
            )

        # has_rating flag
        if "rating" in df.columns:
            df["has_rating"] = df["rating"].notna()

    # ── summary statistics ────────────────────────────────────────────────────

    def summary(self) -> dict:
        df = self.df
        stats: dict = {}

        stats["total_records"]      = len(df)
        stats["unique_products"]    = df["product_name"].nunique() if "product_name" in df.columns else None
        stats["unique_suppliers"]   = df["supplier_name"].nunique() if "supplier_name" in df.columns else None
        stats["categories"]         = df["category"].nunique() if "category" in df.columns else None
        stats["unique_locations"]   = df["location"].nunique() if "location" in df.columns else None

        # price stats
        if "mid_price_inr" in df.columns:
            p = df["mid_price_inr"].dropna()
            stats["price_stats"] = {
                "mean":   round(p.mean(), 2),
                "median": round(p.median(), 2),
                "min":    round(p.min(), 2),
                "max":    round(p.max(), 2),
                "std":    round(p.std(), 2),
            }

        # verified
        if "verified" in df.columns:
            stats["verified_pct"] = round(df["verified"].mean() * 100, 1)

        # missing data
        stats["missing_pct"] = {
            col: round(df[col].isna().mean() * 100, 1)
            for col in df.columns
        }

        return stats

    def category_breakdown(self) -> pd.DataFrame:
        if "category" not in self.df.columns:
            return pd.DataFrame()
        agg = (
            self.df.groupby("category")
            .agg(
                product_count=("product_name", "count"),
                unique_suppliers=("supplier_name", "nunique"),
                avg_min_price=("min_price_inr", "mean"),
                avg_max_price=("max_price_inr", "mean"),
                verified_pct=("verified", lambda s: round(s.mean() * 100, 1)),
                avg_rating=("rating", "mean"),
            )
            .round(2)
            .sort_values("product_count", ascending=False)
        )
        return agg

    def top_locations(self, n: int = 15) -> pd.DataFrame:
        if "location" not in self.df.columns:
            return pd.DataFrame()
        counts = (
            self.df["location"]
            .value_counts()
            .head(n)
            .reset_index()
        )
        counts.columns = ["location", "listing_count"]
        return counts

    def price_distribution_by_category(self) -> pd.DataFrame:
        if "mid_price_inr" not in self.df.columns:
            return pd.DataFrame()
        cols = ["category", "mid_price_inr"] if "category" in self.df.columns else ["mid_price_inr"]
        return (
            self.df[cols]
            .dropna(subset=["mid_price_inr"])
            .groupby("category")["mid_price_inr"]
            .describe(percentiles=[0.25, 0.5, 0.75])
            .round(2)
        )

    def verified_vs_unverified(self) -> pd.DataFrame:
        if "verified" not in self.df.columns or "mid_price_inr" not in self.df.columns:
            return pd.DataFrame()
        return (
            self.df.groupby("verified")
            .agg(
                count=("product_name", "count"),
                avg_price=("mid_price_inr", "mean"),
                avg_rating=("rating", "mean"),
                avg_reviews=("review_count", "mean"),
            )
            .round(2)
        )

    def anomalies(self) -> pd.DataFrame:
        """Flag records that look like data-quality issues."""
        df = self.df.copy()
        issues = []

        if "min_price_inr" in df.columns and "max_price_inr" in df.columns:
            # max < min
            mask = df["max_price_inr"] < df["min_price_inr"]
            subset = df[mask].copy()
            subset["issue"] = "max_price < min_price"
            issues.append(subset)

            # price = 0
            mask2 = (df["min_price_inr"] == 0) | (df["max_price_inr"] == 0)
            subset2 = df[mask2].copy()
            subset2["issue"] = "zero_price"
            issues.append(subset2)

            # extreme outliers (> 5 σ from mean)
            mid = df.get("mid_price_inr")
            if mid is not None:
                mu, sigma = mid.mean(), mid.std()
                mask3 = (mid - mu).abs() > 5 * sigma
                subset3 = df[mask3].copy()
                subset3["issue"] = "price_outlier_5sigma"
                issues.append(subset3)

        if "rating" in df.columns:
            mask4 = df["rating"] > 5
            subset4 = df[mask4].copy()
            subset4["issue"] = "rating_gt_5"
            issues.append(subset4)

        if not issues:
            return pd.DataFrame()
        return pd.concat(issues, ignore_index=True).drop_duplicates()

    def keyword_frequency(self, top_n: int = 20) -> pd.Series:
        """Most common words in product names."""
        if "product_name" not in self.df.columns:
            return pd.Series(dtype=int)
        import re
        stopwords = {
            "the","a","an","and","or","for","in","of","with","to","is","are",
            "from","at","on","by","mm","cm","kg","ml","lt","no","per","set",
        }
        words: list[str] = []
        for name in self.df["product_name"].dropna():
            tokens = re.sub(r"[^a-z0-9\s]", " ", name.lower()).split()
            words.extend(t for t in tokens if t not in stopwords and len(t) > 2)
        return pd.Series(words).value_counts().head(top_n)

    def print_report(self) -> None:
        """Print a human-readable EDA summary to stdout."""
        import sys
        # Ensure UTF-8 output on Windows consoles that default to cp1252
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

        s = self.summary()
        print("=" * 60)
        print("  IndiaMART B2B Marketplace - EDA Report")
        print("=" * 60)
        print(f"  Total records       : {s['total_records']:,}")
        print(f"  Unique products     : {s.get('unique_products', 'N/A')}")
        print(f"  Unique suppliers    : {s.get('unique_suppliers', 'N/A')}")
        print(f"  Categories          : {s.get('categories', 'N/A')}")
        print(f"  Unique locations    : {s.get('unique_locations', 'N/A')}")
        if "verified_pct" in s:
            print(f"  Verified suppliers  : {s['verified_pct']}%")
        if "price_stats" in s:
            ps = s["price_stats"]
            print(f"\n  Price (INR) - mid-point")
            print(f"    Mean   : INR {ps['mean']:>12,.2f}")
            print(f"    Median : INR {ps['median']:>12,.2f}")
            print(f"    Min    : INR {ps['min']:>12,.2f}")
            print(f"    Max    : INR {ps['max']:>12,.2f}")
            print(f"    Std    : INR {ps['std']:>12,.2f}")

        print("\n  Category Breakdown:  (product_count | unique_suppliers | avg_min_price | verified_pct | avg_rating)")
        cb = self.category_breakdown()
        if not cb.empty:
            print(cb.to_string())

        print("\n  Top Locations (by listing count):")
        tl = self.top_locations(10)
        if not tl.empty:
            print(tl.to_string(index=False))

        anom = self.anomalies()
        print(f"\n  Data Quality – Anomalies : {len(anom)} records flagged")
        if not anom.empty:
            print(anom["issue"].value_counts().to_string())

        print("\n  Top Keywords in Product Names:")
        kw = self.keyword_frequency(15)
        if not kw.empty:
            for word, cnt in kw.items():
                bar = "#" * min(cnt // 5, 40)
                print(f"    {word:<20} {cnt:>5}  {bar}")

        print("=" * 60)
