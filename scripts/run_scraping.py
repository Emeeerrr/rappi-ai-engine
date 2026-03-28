"""
Run Scraping - CLI script for competitive data collection.

Usage:
    python scripts/run_scraping.py --use-fallback --output-dir data/competitive/
    python scripts/run_scraping.py --platform rappi --output-dir data/competitive/
    python scripts/run_scraping.py --platform all --output-dir data/competitive/
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path so app imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scraping.addresses import ADDRESSES
from app.scraping.base import BaseScraper


def main():
    parser = argparse.ArgumentParser(description="Rappi Competitive Intelligence - Scraping Runner")
    parser.add_argument(
        "--platform", choices=["rappi", "ubereats", "didi", "all"], default="all",
        help="Platform to scrape (default: all)",
    )
    parser.add_argument(
        "--use-fallback", action="store_true",
        help="Generate realistic dummy data instead of scraping",
    )
    parser.add_argument(
        "--output-dir", default="data/competitive/",
        help="Output directory (default: data/competitive/)",
    )
    parser.add_argument(
        "--no-auto-fallback", action="store_true",
        help="Disable automatic fallback to demo data when scraping fails",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("run_scraping")

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    if args.use_fallback:
        logger.info("Generating fallback (demo) data for %d addresses...", len(ADDRESSES))
        from app.scraping.fallback_data import generate_fallback_data
        results = generate_fallback_data(ADDRESSES)
    else:
        results = []
        scrapers = []

        if args.platform in ("rappi", "all"):
            from app.scraping.rappi import RappiScraper
            scrapers.append(RappiScraper())
        if args.platform in ("ubereats", "all"):
            from app.scraping.ubereats import UberEatsScraper
            scrapers.append(UberEatsScraper())
        if args.platform in ("didi", "all"):
            from app.scraping.didifood import DidiScraper
            scrapers.append(DidiScraper())

        for scraper in scrapers:
            logger.info("Running %s scraper on %d addresses...", scraper.platform_name, len(ADDRESSES))
            results.extend(scraper.run_all(ADDRESSES))

        # Auto-fallback: if >50% failed, switch to demo data
        if results and not args.no_auto_fallback:
            failed_count = sum(1 for r in results if r["scrape_status"] == "failed")
            failure_rate = failed_count / len(results)
            if failure_rate > 0.5:
                logger.warning(
                    "Failure rate %.0f%% > 50%%. Switching to fallback demo data.",
                    failure_rate * 100,
                )
                from app.scraping.fallback_data import generate_fallback_data
                results = generate_fallback_data(ADDRESSES)
                logger.info("Fallback data generated: %d records.", len(results))

    # Save results
    BaseScraper.save_results(results, str(output))

    # Print summary
    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(results)}")

    platforms = set(r["platform"] for r in results)
    for plat in sorted(platforms):
        plat_results = [r for r in results if r["platform"] == plat]
        success = sum(1 for r in plat_results if r["scrape_status"] == "success")
        partial = sum(1 for r in plat_results if r["scrape_status"] == "partial")
        failed = sum(1 for r in plat_results if r["scrape_status"] == "failed")
        print(f"  {plat}: {len(plat_results)} addresses | success={success}, partial={partial}, failed={failed}")

    cities = set(r["city"] for r in results)
    print(f"Cities covered: {len(cities)} ({', '.join(sorted(cities))})")
    print(f"Output: {output.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
