"""
UberEats Scraper - Data collection from Uber Eats Mexico.

This module will implement:
- Restaurant search by address on ubereats.com/mx
- Extraction of: restaurant name, rating, delivery time, delivery fee,
  menu categories, item prices, promotions/discounts
- Handling of Uber Eats specific UI patterns and lazy loading
"""

from app.scraping.base import BaseScraper


class UberEatsScraper(BaseScraper):
    """Scraper for Uber Eats Mexico delivery platform."""

    BASE_URL = "https://www.ubereats.com/mx"

    async def search_restaurants(self, address: str, category: str = None) -> list[dict]:
        """Search restaurants on Uber Eats near the given address."""
        raise NotImplementedError("UberEats scraper not yet implemented")

    async def get_restaurant_details(self, restaurant_url: str) -> dict:
        """Get detailed restaurant info from Uber Eats."""
        raise NotImplementedError("UberEats scraper not yet implemented")
