import asyncio
from typing import List, Optional
from dataclasses import dataclass

from .wildberries_basket import WildberriesBasket
from .wildberries_search import WildberriesSearch
from models import CardDetails, ProductDetails


@dataclass
class BasketConfig:
	"""Configuration options for basket enrichment, including enable flag and concurrency."""

	enabled: bool
	concurrency: int

	def __bool__(self):
		"""Allow BasketConfig to be used directly in boolean checks."""
		return self.enabled


@dataclass
class SearchConfig:
	"""Configuration options for product search, including headless mode and concurrency."""

	headless: bool
	concurrency: int


class Parser:
	"""High-level orchestrator combining search and basket enrichment."""

	def __init__(
		self, search_config: SearchConfig, basket_config: Optional[BasketConfig] = None
	):
		"""Initialize parser with search and optional basket modules."""
		self._wild_search = WildberriesSearch(
			search_config.headless, search_config.concurrency
		)
		self._basket_config = basket_config

		if self._basket_config:
			self._wild_basket = WildberriesBasket()

	async def __aenter__(self):
		"""Async context manager entry point."""
		await self.start()
		return self

	async def __aexit__(self, *args, **kwargs):
		"""Async context manager exit point."""
		await self.close()

	async def start(self):
		"""Start all required subsystems."""
		await self._wild_search.start()

		if hasattr(self, "_wild_basket"):
			await self._wild_basket.start()

	async def close(self):
		"""Gracefully shut down all subsystems."""
		await self._wild_search.close()

		if hasattr(self, "_wild_basket"):
			await self._wild_basket.close()

	async def get_full_products(
		self, query: str, price_min: int, price_max: int, pages_count: int
	) -> List[ProductDetails]:
		"""Fetch products and optionally enrich them with basket data."""
		products = await self._wild_search.search_products(
			query, price_min, price_max, pages_count
		)

		if not self._basket_config:
			return [
				ProductDetails(
					url=card.url,
					article_id=card.article_id,
					name=card.name,
					price=card.price,
					quantity=card.quantity,
					seller_name=card.seller_name,
					seller_url=card.seller_url,
					rating=card.rating,
					feedbacks_count=card.feedbacks_count,
					sizes=card.sizes,
					description=None,
					image_urls=None,
				)
				for card in products
			]

		semaphore = asyncio.Semaphore(self._basket_config.concurrency)

		async def process_one(card: CardDetails):
			"""Enrich a single product with basket data."""
			async with semaphore:
				return await self._wild_basket.enrich(card)

		tasks = [process_one(card) for card in products]
		results = await asyncio.gather(*tasks)

		return results
