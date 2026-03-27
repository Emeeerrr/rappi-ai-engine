"""
Base Scraper - Abstract base class for delivery platform scrapers.

This module will implement:
- Abstract base class with common scraping interface
- Playwright browser session management (headless Chrome)
- Rate limiting and retry logic
- Anti-detection measures (random delays, user-agent rotation)
- Data normalization to a common schema
- Error handling and logging
"""

from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Abstract base class for delivery platform scrapers.

    Subclasses must implement search_restaurants() and get_restaurant_details().
    Provides shared Playwright browser management and rate limiting.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page = None

    @abstractmethod
    async def search_restaurants(self, address: str, category: str = None) -> list[dict]:
        """Search for restaurants near a given address.

        Args:
            address: Delivery address to search from.
            category: Optional category filter.

        Returns:
            List of restaurant dicts with name, rating, delivery_time, delivery_fee, etc.
        """
        ...

    @abstractmethod
    async def get_restaurant_details(self, restaurant_url: str) -> dict:
        """Get detailed info for a specific restaurant.

        Args:
            restaurant_url: URL of the restaurant page.

        Returns:
            Dict with menu items, prices, promotions, ratings, etc.
        """
        ...

    async def start_browser(self) -> None:
        """Initialize Playwright browser session."""
        raise NotImplementedError

    async def close_browser(self) -> None:
        """Close browser and clean up resources."""
        raise NotImplementedError
