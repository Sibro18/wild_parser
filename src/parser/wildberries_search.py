from urllib.parse import urlencode
from typing import List

from config import SEARCH_URL, CATALOG_URL_TEMPLATE, SUPPLIER_URL_TEMPLATE
from models import CardDetails, PriceData
from browser import BrowserManager
from . import utils


class WildberriesSearch:
	"""Handles product search via Wildberries search API."""

	def __init__(self, headless=False, max_concurrent_pages=5):
		"""Initialize search module with browser manager."""
		self.browser_mgr = BrowserManager(headless, 1)

	async def start(self):
		"""Start browser manager."""
		await self.browser_mgr.start()
		print("Browser started")

	async def close(self):
		"""Stop browser manager."""
		await self.browser_mgr.stop()

	async def search_products(
		self, query: str, price_min: int, price_max: int, max_pages: int = 5
	) -> List[CardDetails]:
		"""Search products and return parsed card list."""
		print(f"\nSearch query: {query}")

		return_list: List[CardDetails] = []

		for page_num in range(1, max_pages + 1):
			print(f"\tPage {page_num}...")

			results = await self._fetch_search_page(
				query=query, price_min=price_min, price_max=price_max, page_num=page_num
			)

			if not results:
				print(f"\tNo data on page {page_num}")
				continue

			added = 0
			denied = 0

			for product in results:
				if product.get("reviewRating", 0) >= 4.5:
					return_list.append(self._parse_product(product))
					added += 1
				else:
					denied += 1

			print(f"\tAdded {added} products")
			print(f"\tDenied {denied} products")

		print(f"Total collected cards: {len(return_list)}")

		return return_list

	async def _fetch_search_page(
		self, query: str, price_min: int, price_max: int, page_num: int
	) -> List[dict]:
		"""Fetch a single search page and extract product list."""
		page = await self.browser_mgr.pool.get_page()

		try:
			url = self._build_search_url(query, price_min, price_max, page_num)

			async with page.expect_response(
				lambda r: r.url.startswith(SEARCH_URL) and f"page={page_num}" in r.url,
				timeout=30000,
			) as resp_info:
				await page.goto(url)

			response = await resp_info.value

			data = await utils.safe_json(response)
			if data:
				return data.get("products", [])

			text = await utils.safe_text(response)
			if text:
				data = utils.safe_parse_json(text)
				if data:
					return data.get("products", [])

			pre = await utils.safe_pre(page)
			if pre:
				data = utils.safe_parse_json(pre)
				if data:
					return data.get("products", [])

			return []

		except Exception as exc:
			print(f"Error on page {page_num}: {exc}")
			return []

		finally:
			await self.browser_mgr.pool.release_page(page)

	def _build_search_url(
		self, query: str, price_min: int, price_max: int, page_num: int
	) -> str:
		"""Build a valid Wildberries search URL."""
		params = {
			"appType": 1,
			"curr": "rub",
			"dest": -3217375,
			"lang": "ru",
			"page": page_num,
			"query": query,
			"priceU": f"{price_min};{price_max}",
			"resultset": "catalog",
			"sort": "rate",
			"spp": 30,
		}
		self._add_filter(params, 14177451, 15000203)  # Production Country = Russia.

		return f"{SEARCH_URL}?{urlencode(params)}"

	def _add_filter(self, params: dict, filter_id: int, value: int):
		"""Add filter to request params."""
		params[f"f{filter_id}"] = value

	def _parse_product(self, product: dict) -> CardDetails:
		"""Convert raw product JSON into CardDetails model."""
		article_id = product["id"]
		sizes_data = product.get("sizes", [])
		size_names = []
		quantity = product.get("totalQuantity", 0)
		price = {}
		for s in sizes_data:
			name = s.get("name", "")
			size_names.append(name)
			basic = s.get("price", {}).get("basic", 0) // 100
			product_price = s.get("price", {}).get("product", 0) // 100
			price[name] = PriceData(basic=basic, product=product_price)

		return CardDetails(
			url=CATALOG_URL_TEMPLATE.format(article_id),
			article_id=article_id,
			name=product.get("name", ""),
			price=price,
			quantity=quantity,
			seller_name=product.get("supplier", ""),
			seller_url=SUPPLIER_URL_TEMPLATE.format(product.get("supplierId", "")),
			rating=product.get("reviewRating", 0.0),
			feedbacks_count=product.get("feedbacks", 0),
			sizes=size_names,
		)
