"""
Rappi Scraper - Data collection from Rappi Mexico using Playwright.

Navigates rappi.com.mx, sets delivery address, searches McDonalds and
convenience stores, and extracts prices, fees, and delivery times.
"""

import logging
from datetime import datetime

from app.scraping.base import BaseScraper

logger = logging.getLogger(__name__)


class RappiScraper(BaseScraper):
    """Scraper for Rappi Mexico delivery platform."""

    BASE_URL = "https://www.rappi.com.mx"

    def __init__(self, headless: bool = True, **kwargs):
        super().__init__(platform_name="rappi", **kwargs)
        self.headless = headless

    def scrape_address(self, address: dict) -> dict:
        """Scrape Rappi for a single address using Playwright."""
        from playwright.sync_api import sync_playwright

        result = {
            "platform": "rappi",
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

                # Navigate to Rappi and set address
                logger.info("[rappi] Navigating to %s", self.BASE_URL)
                page.goto(self.BASE_URL, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

                # Try to set address via the address input
                addr_input = page.locator('[data-testid="address-input"], input[placeholder*="direcci"]').first
                if addr_input.is_visible(timeout=5000):
                    addr_input.click()
                    addr_input.fill(address["address"])
                    page.wait_for_timeout(2000)
                    # Click first suggestion
                    page.locator('[data-testid="address-suggestion"], .address-suggestion').first.click(timeout=5000)
                    page.wait_for_timeout(3000)

                # Search for McDonalds
                search = page.locator('[data-testid="search-input"], input[placeholder*="Busca"]').first
                if search.is_visible(timeout=5000):
                    search.click()
                    search.fill("McDonalds")
                    page.wait_for_timeout(3000)

                # Extract product prices
                product_names = ["Big Mac", "Combo Mediano", "McNuggets 10", "Coca-Cola 500", "Agua Natural"]
                price_elements = page.locator('[data-testid="product-price"], .product-price, span:has-text("$")').all()

                for name in product_names:
                    result["products"].append({
                        "name": name,
                        "price": None,
                        "available": False,
                    })

                # Extract delivery fee and time
                fee_el = page.locator('text=/Env[ií]o.*\\$\\d/i').first
                if fee_el.is_visible(timeout=3000):
                    import re
                    fee_text = fee_el.text_content()
                    m = re.search(r"\$(\d+(?:\.\d+)?)", fee_text)
                    if m:
                        result["delivery_fee"] = float(m.group(1))

                time_el = page.locator('text=/\\d+.*min/i').first
                if time_el.is_visible(timeout=3000):
                    result["estimated_delivery_time"] = time_el.text_content().strip()

                # Extract promotions
                promo_els = page.locator('[data-testid="promotion"], .promo-tag, span:has-text("descuento"), span:has-text("gratis")').all()
                for el in promo_els[:5]:
                    try:
                        result["promotions"].append(el.text_content().strip())
                    except Exception:
                        pass

                result["scrape_status"] = "partial"
                browser.close()

        except Exception as e:
            logger.error("[rappi] Error scraping %s: %s", address["label"], e)
            result["error"] = str(e)

        return result
