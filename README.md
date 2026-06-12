# IndiaMART B2B Data Engineering Challenge

End-to-end pipeline: **crawl → extract → clean → analyse → visualise**.

## Project Structure

```
.
├── scraper/
│   ├── config.py       # All tuneable settings in one place
│   ├── crawler.py      # HTTP orchestrator with retry + rate-limiting
│   ├── extractors.py   # BeautifulSoup HTML parsers for IndiaMART
│   ├── mock_data.py    # Synthetic dataset generator (fallback)
│   ├── storage.py      # Load/save JSON & CSV helpers
│   └── utils.py        # Logging, user-agent rotation, price parsing
├── eda/
│   ├── analysis.py     # EDAAnalyzer class (stats + anomaly detection)
│   └── visualizations.py  # 10 Matplotlib/Seaborn chart generators
├── notebooks/
│   └── eda_analysis.ipynb  # Full interactive EDA walkthrough
├── data/
│   ├── raw/            # Scraped JSON files (created at runtime)
│   └── processed/      # Cleaned CSV/JSON + chart PNGs
├── main.py             # CLI entry point
└── requirements.txt
```

## Quick Start

### 1. Install dependencies

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the full pipeline

```bash
# Option A: live scraping (auto-falls back to synthetic data if blocked)
python main.py

# Option B: synthetic dataset (no network calls — great for demos)
python main.py --mock

# Option C: EDA only on existing scraped data
python main.py --eda-only

# Limit pages per category (faster runs)
python main.py --mock --pages 2
```

### 3. Open the Jupyter notebook

```bash
jupyter notebook notebooks/eda_analysis.ipynb
```

## Output

| Artifact | Location |
|---|---|
| Raw scraped JSON | `data/raw/products_YYYYMMDD_HHMMSS.json` |
| Cleaned CSV | `data/processed/products_YYYYMMDD_HHMMSS.csv` |
| Cleaned JSON | `data/processed/products_YYYYMMDD_HHMMSS.json` |
| Charts (10 PNGs) | `data/processed/charts/` |

## Scraper Design

### Target Site
IndiaMART (`dir.indiamart.com`) — India's largest B2B marketplace.

### Categories Scraped
| # | Category | Query |
|---|---|---|
| 1 | Industrial Machinery | `industrial+machinery` |
| 2 | Electronics | `electronics+components` |
| 3 | Textiles & Apparel | `textiles+fabric` |
| 4 | Chemical & Pharma | `chemical+raw+material` |
| 5 | Agricultural Products | `agricultural+products` |

### Anti-blocking Measures
- **User-agent rotation** — 7 real browser UA strings
- **Randomised delays** — 2–5 s between requests (configurable)
- **Retry with backoff** — up to 3 retries, 4–10 s wait (via `tenacity`)
- **Session reuse** — single `requests.Session` with persistent headers
- **Automatic fallback** — switches to synthetic data if 2 consecutive categories return 0 results

### Extracted Fields

| Field | Description |
|---|---|
| `product_name` | Product listing title |
| `category` | Scraped category |
| `min_price_inr` / `max_price_inr` | Price range in INR |
| `price_unit` | Unit of sale (Piece, Kg, Meter, …) |
| `supplier_name` | Company name |
| `location` | Supplier city |
| `state` | Supplier state (synthetic data) |
| `verified` | Whether the supplier is IndiaMART-verified |
| `rating` | Supplier star rating (1–5) |
| `review_count` | Number of reviews |
| `min_order_qty` | Minimum order quantity |
| `description` | Product description snippet |
| `product_url` | Link to product detail page |
| `scraped_at` | UTC timestamp |

## EDA Highlights

### Charts Generated
1. Category distribution (horizontal bar)
2. Price distribution by category (box plot, log scale)
3. Top 15 supplier cities
4. Verified vs unverified suppliers (pie)
5. Rating distribution (histogram)
6. Price heatmap — category × city
7. Product name word cloud
8. Review count vs. rating (scatter)
9. Price spread % distribution
10. State-level supplier count

### Key Insights
- **Gujarat dominates** supplier listings (Ahmedabad, Surat, Rajkot) — India's manufacturing heartland
- **Industrial Machinery** has the widest price range (₹15k–₹5M), reflecting diverse equipment types
- **Verified suppliers** average higher ratings and more reviews — quality signal for buyers
- **~30% of listings lack ratings** — many suppliers don't actively collect feedback
- **Electronics** shows the highest price spread %, indicating significant quality/brand tiers

## Configuration

All scraper settings live in `scraper/config.py`:

```python
ScraperConfig(
    max_pages_per_category = 5,    # pages to paginate per category
    min_delay_seconds = 2.0,       # min sleep between requests
    max_delay_seconds = 5.0,       # max sleep between requests
    max_retries = 3,               # retry attempts on failure
)
```
