"""
DiDi Food Scraper - Data collection from DiDi Food Mexico.

This module will implement:
- Restaurant search by address on didifood.com/mx
- Extraction of: restaurant name, rating, delivery time, delivery fee,
  menu categories, item prices, promotions/discounts
- Handling of DiDi Food specific UI patterns
"""

from app.scraping.base import BaseScraper


class DidiScraper(BaseScraper):
    """Scraper for DiDi Food Mexico delivery platform."""

    BASE_URL = "https://www.didifood.com/mx"

    async def search_restaurants(self, address: str, category: str = None) -> list[dict]:
        """Search restaurants on DiDi Food near the given address."""
        raise NotImplementedError("DiDi Food scraper not yet implemented")

    async def get_restaurant_details(self, restaurant_url: str) -> dict:
        """Get detailed restaurant info from DiDi Food."""
        raise NotImplementedError("DiDi Food scraper not yet implemented")
