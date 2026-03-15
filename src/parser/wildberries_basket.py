import asyncio
import aiohttp
from typing import List, Optional

from config import BASKET_URL_TEMPLATE
from models import CardDetails, ProductDetails


class WildberriesBasket:
	"""Handles basket API lookups for product details and images."""

	def __init__(self):
		"""Initialize basket client without starting HTTP session."""
		self.http_session = None

	async def start(self):
		"""Create aiohttp session."""
		self.http_session = aiohttp.ClientSession()

	async def close(self):
		"""Close aiohttp session."""
		await self.http_session.close()

	async def enrich(self, card: CardDetails) -> ProductDetails:
		"""Enrich product with description and images from basket."""
		print("enriching with basket: ", card.article_id)

		basket_url = await self._find_basket_url(card.article_id)
		description = None
		images = None

		if basket_url:
			basket_card = await self._get_basket_card(basket_url)
			if basket_card:
				description = basket_card.get("description")

			images = await self._get_basket_images(basket_url)

		return ProductDetails(
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
			description=description,
			image_urls=images,
		)

	async def _find_basket_url(
		self, article_id: int, max_attempts: int = 100
	) -> Optional[str]:
		"""Find the correct basket URL by probing multiple buckets."""
		vol = article_id // 100_000
		part = article_id // 1_000

		async def check(basket_num: int) -> Optional[str]:
			"""Check if a specific basket bucket contains the product."""
			num = f"{basket_num:02d}"
			base = BASKET_URL_TEMPLATE.format(num, vol, part, article_id)
			url = f"{base}/info/ru/card.json"

			try:
				async with self.http_session.get(url, timeout=3) as resp:
					if resp.status < 400:
						return base
			except aiohttp.ClientError:
				return None

		tasks = [check(i) for i in range(1, max_attempts + 1)]

		for cor in asyncio.as_completed(tasks):
			result = await cor
			if result:
				return result

		return None

	async def _get_basket_card(self, basket_url: str) -> Optional[dict]:
		"""Fetch basket card JSON data."""
		url = basket_url + "/info/ru/card.json"
		try:
			async with self.http_session.get(url, timeout=5) as resp:
				if resp.status < 400:
					return await resp.json()
		except Exception:
			return None

	async def _get_basket_images(self, basket_url: str) -> List[str]:
		"""Fetch all available product images from basket."""
		urls = []
		i = 1

		while True:
			img_url = f"{basket_url}/images/big/{i}.webp"
			try:
				async with self.http_session.head(img_url, timeout=2) as resp:
					if resp.status < 400:
						urls.append(img_url)
					else:
						break
				i += 1
			except Exception:
				break
		return urls
