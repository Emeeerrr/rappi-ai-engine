"""
Rappi Scraper - Data collection from Rappi Mexico.

This module will implement:
- Restaurant search by address on rappi.com.mx
- Extraction of: restaurant name, rating, delivery time, delivery fee,
  menu categories, item prices, promotions/discounts
- Pagination handling for restaurant listings
- Category-specific searches (restaurants, groceries, etc.)
"""

from app.scraping.base import BaseScraper


class RappiScraper(BaseScraper):
    """Scraper for Rappi Mexico delivery platform."""

    BASE_URL = "https://www.rappi.com.mx"

    async def search_restaurants(self, address: str, category: str = None) -> list[dict]:
        """Search restaurants on Rappi near the given address."""
        raise NotImplementedError("Rappi scraper not yet implemented")

    async def get_restaurant_details(self, restaurant_url: str) -> dict:
        """Get detailed restaurant info from Rappi."""
        raise NotImplementedError("Rappi scraper not yet implemented")
