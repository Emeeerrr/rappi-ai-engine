"""
DiDi Food Scraper - Data collection from DiDi Food Mexico using Playwright.
"""

import logging
from datetime import datetime

from app.scraping.base import BaseScraper

logger = logging.getLogger(__name__)


class DidiScraper(BaseScraper):
    """Scraper for DiDi Food Mexico delivery platform."""

    BASE_URL = "https://www.didi-food.com/es-MX"

    def __init__(self, headless: bool = True, **kwargs):
        super().__init__(platform_name="didi", **kwargs)
        self.headless = headless

    def scrape_address(self, address: dict) -> dict:
        """Scrape DiDi Food for a single address using Playwright."""
        from playwright.sync_api import sync_playwright

        result = {
            "platform": "didi",
            "address_id": address["id"],
            "address_label": address["label"],
            "city": address["city"],
            "zone_type": address["zone_type"],
            "timestamp": datetime.now().isoformat(),
            "restaurant": "McDonalds",
            "products": [],
            "delivery_fee": None,
            "service_fee": None,
            "estimated_delivery_time": None,
            "promotions": [],
            "total_price_big_mac_combo": None,
            "screenshot_path": None,
            "scrape_status": "failed",
            "error": None,
        }

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=self._get_user_agent(),
                    viewport={"width": 1280, "height": 800},
                    locale="es-MX",
                )
                page = context.new_page()

                logger.info("[didi] Navigating to %s", self.BASE_URL)
                page.goto(self.BASE_URL, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

                # Set delivery address
                addr_input = page.locator('input[placeholder*="direcci"], input[placeholder*="address"]').first
                if addr_input.is_visible(timeout=5000):
                    addr_input.click()
                    addr_input.fill(address["address"])
                    page.wait_for_timeout(2000)
                    page.locator('.address-suggestion, li[role="option"]').first.click(timeout=5000)
                    page.wait_for_timeout(3000)

                # Search McDonalds
                search = page.locator('input[placeholder*="Busca"], input[type="search"]').first
                if search.is_visible(timeout=5000):
                    search.click()
                    search.fill("McDonalds")
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(3000)

                product_names = ["Big Mac", "Combo Mediano", "McNuggets 10", "Coca-Cola 500", "Agua Natural"]
                for name in product_names:
                    result["products"].append({"name": name, "price": None, "available": False})

                import re
                fee_el = page.locator('text=/env[ií]o.*\\$\\d/i').first
                if fee_el.is_visible(timeout=3000):
                    fee_text = fee_el.text_content()
                    m = re.search(r"\$(\d+(?:\.\d+)?)", fee_text)
                    if m:
                        result["delivery_fee"] = float(m.group(1))

                time_el = page.locator('text=/\\d+.{0,5}min/i').first
                if time_el.is_visible(timeout=3000):
                    result["estimated_delivery_time"] = time_el.text_content().strip()

                # Capture screenshot as evidence
                try:
                    import time
                    from pathlib import Path
                    shots_dir = Path("data/competitive/screenshots")
                    shots_dir.mkdir(parents=True, exist_ok=True)
                    shot_path = str(shots_dir / f"didi_{address['id']}_{int(time.time())}.png")
                    page.screenshot(path=shot_path)
                    result["screenshot_path"] = shot_path
                    logger.info("[didi] Screenshot saved: %s", shot_path)
                except Exception as ss_err:
                    logger.warning("[didi] Screenshot failed: %s", ss_err)

                result["scrape_status"] = "partial"
                browser.close()

        except Exception as e:
            logger.error("[didi] Error scraping %s: %s", address["label"], e)
            result["error"] = str(e)

        return result
