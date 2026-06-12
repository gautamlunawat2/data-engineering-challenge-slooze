"""
Chart generation for the EDA pipeline.

Each function saves a PNG to *output_dir* and returns the file path.
All charts are self-contained (no global state, no plt.show calls) so
they work cleanly in both script mode and Jupyter notebooks.
"""
from __future__ import annotations

import os
from typing import Optional

import matplotlib
matplotlib.use("Agg")          # non-interactive backend for script mode
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

_PALETTE = "husl"
_FIGSIZE = (12, 7)
_DPI = 120
_OUTPUT_DIR = "data/processed/charts"


def _save(fig: plt.Figure, name: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{name}.png")
    fig.savefig(path, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    return path


# ── 1. Products per category (bar) ───────────────────────────────────────────

def plot_category_distribution(df: pd.DataFrame,
                                output_dir: str = _OUTPUT_DIR) -> str:
    counts = df["category"].value_counts()
    fig, ax = plt.subplots(figsize=_FIGSIZE)
    colors = sns.color_palette(_PALETTE, len(counts))
    bars = ax.barh(counts.index, counts.values, color=colors, edgecolor="white")
    ax.bar_label(bars, padding=4, fmt="%d", fontsize=9)
    ax.set_xlabel("Number of Listings")
    ax.set_title("Product Listings by Category", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return _save(fig, "01_category_distribution", output_dir)


# ── 2. Price distribution per category (box plot) ────────────────────────────

def plot_price_boxplot(df: pd.DataFrame,
                       output_dir: str = _OUTPUT_DIR) -> str:
    if "mid_price_inr" not in df.columns or "category" not in df.columns:
        return ""
    plot_df = df[["category", "mid_price_inr"]].dropna()
    # log-scale for readability across wide price ranges
    plot_df = plot_df.assign(log_price=np.log10(plot_df["mid_price_inr"].clip(lower=1)))

    order = (
        plot_df.groupby("category")["log_price"]
        .median()
        .sort_values(ascending=False)
        .index
    )
    fig, ax = plt.subplots(figsize=_FIGSIZE)
    sns.boxplot(data=plot_df, x="log_price", y="category", order=order,
                palette=_PALETTE, linewidth=0.8, ax=ax)
    ax.set_xlabel("Price (INR, log₁₀ scale)")
    ax.set_title("Price Distribution by Category", fontsize=14, fontweight="bold")
    ticks = [1, 2, 3, 4, 5, 6, 7]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"₹{10**t:,.0f}" for t in ticks], fontsize=8)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return _save(fig, "02_price_boxplot", output_dir)


# ── 3. Top supplier locations (bar chart) ────────────────────────────────────

def plot_top_locations(df: pd.DataFrame,
                       output_dir: str = _OUTPUT_DIR,
                       top_n: int = 15) -> str:
    if "location" not in df.columns:
        return ""
    counts = df["location"].value_counts().head(top_n)
    fig, ax = plt.subplots(figsize=_FIGSIZE)
    colors = sns.color_palette("Blues_r", top_n)
    bars = ax.bar(counts.index, counts.values, color=colors, edgecolor="white")
    ax.bar_label(bars, padding=3, fmt="%d", fontsize=8)
    ax.set_xlabel("City")
    ax.set_ylabel("Number of Listings")
    ax.set_title(f"Top {top_n} Supplier Locations", fontsize=14, fontweight="bold")
    plt.xticks(rotation=40, ha="right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return _save(fig, "03_top_locations", output_dir)


# ── 4. Verified vs unverified suppliers (pie) ────────────────────────────────

def plot_verified_pie(df: pd.DataFrame,
                      output_dir: str = _OUTPUT_DIR) -> str:
    if "verified" not in df.columns:
        return ""
    counts = df["verified"].value_counts()
    labels = ["Verified" if v else "Unverified" for v in counts.index]
    colors = ["#2ecc71", "#e74c3c"]
    fig, ax = plt.subplots(figsize=(7, 7))
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=labels, colors=colors,
        autopct="%1.1f%%", startangle=140,
        wedgeprops=dict(edgecolor="white", linewidth=2)
    )
    for at in autotexts:
        at.set_fontsize(13)
    ax.set_title("Verified vs. Unverified Suppliers", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return _save(fig, "04_verified_pie", output_dir)


# ── 5. Rating distribution (histogram) ───────────────────────────────────────

def plot_rating_distribution(df: pd.DataFrame,
                              output_dir: str = _OUTPUT_DIR) -> str:
    if "rating" not in df.columns:
        return ""
    ratings = df["rating"].dropna()
    if ratings.empty:
        return ""
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(ratings, bins=20, color="#3498db", edgecolor="white", alpha=0.85)
    ax.axvline(ratings.mean(), color="#e74c3c", linestyle="--",
               label=f"Mean = {ratings.mean():.2f}")
    ax.axvline(ratings.median(), color="#f39c12", linestyle="--",
               label=f"Median = {ratings.median():.2f}")
    ax.set_xlabel("Rating (out of 5)")
    ax.set_ylabel("Count")
    ax.set_title("Supplier Rating Distribution", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return _save(fig, "05_rating_distribution", output_dir)


# ── 6. Heatmap – avg price by (category × location) ─────────────────────────

def plot_price_heatmap(df: pd.DataFrame,
                       output_dir: str = _OUTPUT_DIR,
                       top_locations: int = 10) -> str:
    cols = ["category", "location", "mid_price_inr"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        return ""

    top_locs = df["location"].value_counts().head(top_locations).index
    pivot_df = (
        df[df["location"].isin(top_locs)][cols]
        .dropna()
        .groupby(["category", "location"])["mid_price_inr"]
        .median()
        .unstack("location")
        .fillna(0)
    )
    if pivot_df.empty:
        return ""

    fig, ax = plt.subplots(figsize=(14, 6))
    log_pivot = np.log10(pivot_df.replace(0, np.nan))
    _fmt_fn = getattr(pivot_df, "map", getattr(pivot_df, "applymap", None))
    sns.heatmap(log_pivot, annot=_fmt_fn(lambda v: f"INR {v:,.0f}"),
                fmt="s", cmap="YlOrRd", linewidths=0.5, ax=ax,
                cbar_kws={"label": "Median Price INR (log₁₀)"})
    ax.set_title("Median Price Heatmap – Category × City", fontsize=13, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.xticks(rotation=35, ha="right", fontsize=9)
    plt.yticks(fontsize=9)
    fig.tight_layout()
    return _save(fig, "06_price_heatmap", output_dir)


# ── 7. Word cloud for product names ──────────────────────────────────────────

def plot_wordcloud(df: pd.DataFrame,
                   output_dir: str = _OUTPUT_DIR) -> str:
    if "product_name" not in df.columns:
        return ""
    try:
        from wordcloud import WordCloud
    except ImportError:
        return ""

    import re
    stopwords = {
        "the","a","an","and","or","for","in","of","with","to","is","are",
        "from","at","on","by","mm","cm","kg","ml","lt","no","per","set",
        "pack","grade","type","quality","industrial","product",
    }
    text = " ".join(df["product_name"].dropna().tolist()).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = [w for w in text.split() if w not in stopwords and len(w) > 2]
    text_clean = " ".join(words)

    wc = WordCloud(width=1200, height=600, background_color="white",
                   colormap="tab10", max_words=120).generate(text_clean)
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Product Name Word Cloud", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return _save(fig, "07_wordcloud", output_dir)


# ── 8. Review count vs. rating (scatter) ─────────────────────────────────────

def plot_reviews_vs_rating(df: pd.DataFrame,
                           output_dir: str = _OUTPUT_DIR) -> str:
    cols = ["rating", "review_count"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        return ""
    plot_df = df[cols + (["category"] if "category" in df.columns else [])].dropna()
    if plot_df.empty:
        return ""

    fig, ax = plt.subplots(figsize=(9, 6))
    if "category" in plot_df.columns:
        categories = plot_df["category"].unique()
        palette = dict(zip(categories, sns.color_palette(_PALETTE, len(categories))))
        for cat, grp in plot_df.groupby("category"):
            ax.scatter(grp["review_count"], grp["rating"],
                       label=cat, alpha=0.55, s=30, color=palette[cat])
        ax.legend(fontsize=7, ncol=2)
    else:
        ax.scatter(plot_df["review_count"], plot_df["rating"],
                   alpha=0.5, s=30, color="#3498db")

    ax.set_xlabel("Review Count")
    ax.set_ylabel("Rating")
    ax.set_title("Review Count vs. Rating", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _save(fig, "08_reviews_vs_rating", output_dir)


# ── 9. Price spread percentage distribution ───────────────────────────────────

def plot_price_spread(df: pd.DataFrame,
                      output_dir: str = _OUTPUT_DIR) -> str:
    if "price_spread_pct" not in df.columns:
        return ""
    data = df["price_spread_pct"].replace([np.inf, -np.inf], np.nan).dropna()
    data = data[data < 500]   # exclude extreme outliers for readability
    if data.empty:
        return ""

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(data, bins=40, color="#9b59b6", edgecolor="white", alpha=0.85)
    ax.axvline(data.median(), color="#e74c3c", linestyle="--",
               label=f"Median = {data.median():.1f}%")
    ax.set_xlabel("Price Spread (%)")
    ax.set_ylabel("Count")
    ax.set_title("Price Range Spread Distribution\n(max - min) / min × 100",
                 fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return _save(fig, "09_price_spread", output_dir)


# ── 10. State-level supplier count (horizontal bar) ──────────────────────────

def plot_state_distribution(df: pd.DataFrame,
                             output_dir: str = _OUTPUT_DIR) -> str:
    if "state" not in df.columns:
        return ""
    counts = df["state"].value_counts().head(15)
    fig, ax = plt.subplots(figsize=_FIGSIZE)
    colors = sns.color_palette("viridis", len(counts))
    bars = ax.barh(counts.index, counts.values, color=colors, edgecolor="white")
    ax.bar_label(bars, padding=4, fmt="%d", fontsize=9)
    ax.set_xlabel("Number of Listings")
    ax.set_title("Supplier Listings by State", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return _save(fig, "10_state_distribution", output_dir)


# ── master runner ─────────────────────────────────────────────────────────────

def generate_all_charts(df: pd.DataFrame,
                         output_dir: str = _OUTPUT_DIR) -> dict[str, str]:
    """
    Run all chart generators and return a dict mapping chart name → file path.
    Charts with missing columns are silently skipped.
    """
    from scraper.utils import get_logger
    log = get_logger(__name__)

    fns = [
        ("category_distribution",  plot_category_distribution),
        ("price_boxplot",          plot_price_boxplot),
        ("top_locations",          plot_top_locations),
        ("verified_pie",           plot_verified_pie),
        ("rating_distribution",    plot_rating_distribution),
        ("price_heatmap",          plot_price_heatmap),
        ("wordcloud",              plot_wordcloud),
        ("reviews_vs_rating",      plot_reviews_vs_rating),
        ("price_spread",           plot_price_spread),
        ("state_distribution",     plot_state_distribution),
    ]

    results: dict[str, str] = {}
    for name, fn in fns:
        try:
            path = fn(df, output_dir=output_dir)
            if path:
                results[name] = path
                log.info("Chart saved: %s", path)
        except Exception as exc:  # noqa: BLE001
            log.warning("Chart '%s' failed: %s", name, exc)

    return results
