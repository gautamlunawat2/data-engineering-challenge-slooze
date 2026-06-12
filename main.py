from __future__ import annotations

import argparse
import sys

from scraper import IndiaMArtCrawler, ScraperConfig
from scraper.storage import load_raw_json, to_dataframe, save_processed
from scraper.utils import get_logger
from eda import EDAAnalyzer
from eda.visualizations import generate_all_charts

logger = get_logger("main")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="IndiaMART B2B scraper + EDA pipeline")
    p.add_argument("--mock",     action="store_true",
                   help="Use synthetic data instead of live scraping")
    p.add_argument("--eda-only", action="store_true",
                   help="Skip scraping; run EDA on existing raw data")
    p.add_argument("--pages",    type=int, default=5,
                   help="Max pages to scrape per category (default: 5)")
    p.add_argument("--no-charts", action="store_true",
                   help="Skip chart generation")
    return p.parse_args()


def run_scraper(mock: bool, pages: int) -> list[dict]:
    cfg = ScraperConfig(max_pages_per_category=pages)
    crawler = IndiaMArtCrawler(config=cfg)
    logger.info("Starting scraper (mock=%s)", mock)
    return crawler.run(mock=mock)


def run_eda(records: list[dict], charts: bool = True) -> None:
    if not records:
        logger.error("No records to analyse. Exiting.")
        sys.exit(1)

    df = to_dataframe(records)
    logger.info("DataFrame shape: %s", df.shape)

    paths = save_processed(df)
    logger.info("Processed data saved: %s", paths)

    analyzer = EDAAnalyzer(df)
    analyzer.print_report()

    if charts:
        logger.info("Generating charts …")
        # Use the enriched df (contains mid_price_inr, price_spread_pct, etc.)
        chart_paths = generate_all_charts(analyzer.df)
        logger.info("Generated %d charts:", len(chart_paths))
        for name, path in chart_paths.items():
            logger.info("  %-28s → %s", name, path)


def main() -> None:
    args = parse_args()

    if args.eda_only:
        logger.info("EDA-only mode: loading existing raw data")
        records = load_raw_json()
    else:
        records = run_scraper(mock=args.mock, pages=args.pages)

    run_eda(records, charts=not args.no_charts)


if __name__ == "__main__":
    main()
