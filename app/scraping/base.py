"""
Base Scraper - Abstract base class for delivery platform scrapers.

Provides rate limiting, retry logic, user-agent rotation, result persistence,
and a run_all() orchestrator. Subclasses implement scrape_address().
"""

import json
import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


class BaseScraper(ABC):
    """Abstract base class for delivery platform scrapers.

    Args:
        platform_name: Identifier for the platform (rappi, ubereats, didi).
        rate_limit: Seconds to wait between requests.
        max_retries: Maximum retry attempts per address.
    """

    def __init__(self, platform_name: str, rate_limit: float = 3.0, max_retries: int = 3):
        self.platform_name = platform_name
        self.rate_limit = rate_limit
        self.max_retries = max_retries

    def _get_user_agent(self) -> str:
        return random.choice(USER_AGENTS)

    @abstractmethod
    def scrape_address(self, address: dict) -> dict:
        """Scrape data for a single address. Must return the standard result dict."""
        ...

    def run_all(self, addresses: list[dict]) -> list[dict]:
        """Scrape all addresses with rate limiting and retries.

        Returns:
            List of result dicts, one per address.
        """
        results = []
        total = len(addresses)
        success = 0
        failed = 0

        for idx, addr in enumerate(addresses, 1):
            logger.info(
                "[%s] Scraping %d/%d: %s", self.platform_name, idx, total, addr["label"],
            )

            result = None
            for attempt in range(1, self.max_retries + 1):
                try:
                    result = self.scrape_address(addr)
                    if result.get("scrape_status") != "failed":
                        break
                except Exception as e:
                    logger.warning(
                        "[%s] Attempt %d/%d failed for %s: %s",
                        self.platform_name, attempt, self.max_retries, addr["label"], e,
                    )
                    if attempt < self.max_retries:
                        wait = 2 ** attempt
                        logger.info("Retrying in %ds...", wait)
                        time.sleep(wait)
                    else:
                        result = self._error_result(addr, str(e))

            if result is None:
                result = self._error_result(addr, "No result returned")

            results.append(result)

            if result.get("scrape_status") == "failed":
                failed += 1
            else:
                success += 1

            if idx < total:
                time.sleep(self.rate_limit)

        logger.info(
            "[%s] Scraping complete: %d success, %d failed out of %d",
            self.platform_name, success, failed, total,
        )
        return results

    def _error_result(self, address: dict, error_msg: str) -> dict:
        return {
            "platform": self.platform_name,
            "address_id": address["id"],
            "address_label": address["label"],
            "city": address["city"],
            "zone_type": address["zone_type"],
            "timestamp": datetime.now().isoformat(),
            "restaurant": None,
            "products": [],
            "delivery_fee": None,
            "service_fee": None,
            "estimated_delivery_time": None,
            "promotions": [],
            "total_price_big_mac_combo": None,
            "screenshot_path": None,
            "scrape_status": "failed",
            "error": error_msg,
        }

    @staticmethod
    def save_results(results: list[dict], output_path: str) -> None:
        """Save results as both JSON and CSV."""
        out = Path(output_path)
        out.mkdir(parents=True, exist_ok=True)

        # JSON (full fidelity)
        json_path = out / "competitive_data.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info("Saved JSON: %s (%d records)", json_path, len(results))

        # CSV (flattened for easy analysis)
        rows = []
        for r in results:
            base = {
                "platform": r.get("platform"),
                "address_id": r.get("address_id"),
                "address_label": r.get("address_label"),
                "city": r.get("city"),
                "zone_type": r.get("zone_type"),
                "timestamp": r.get("timestamp"),
                "restaurant": r.get("restaurant"),
                "delivery_fee": r.get("delivery_fee"),
                "service_fee": r.get("service_fee"),
                "estimated_delivery_time": r.get("estimated_delivery_time"),
                "promotions": "; ".join(r.get("promotions") or []),
                "total_price_big_mac_combo": r.get("total_price_big_mac_combo"),
                "scrape_status": r.get("scrape_status"),
                "error": r.get("error"),
            }
            for p in r.get("products", []):
                row = {**base, "product_name": p["name"], "product_price": p.get("price"), "product_available": p.get("available")}
                rows.append(row)
            if not r.get("products"):
                rows.append(base)

        csv_path = out / "competitive_data.csv"
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        logger.info("Saved CSV: %s (%d rows)", csv_path, len(rows))
