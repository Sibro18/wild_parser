import asyncio
import os
from parser import Parser, BasketConfig, SearchConfig
from excel import save_to_excel


async def main():
	# Settings
	HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
	MAX_CONCURRENT_ASYNC_TASKS = int(os.getenv("MAX_CONCURRENT_ASYNC_TASKS", "5"))
	MAX_CONCURRENT_PAGES = int(os.getenv("MAX_CONCURRENT_PAGES", "5"))
	WITH_BASKET = os.getenv("WITH_BASKET", "true").lower() == "true"
	MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))

	QUERY = os.getenv("QUERY", "пальто из натуральной шерсти")
	PRICE_MIN = int(os.getenv("PRICE_MIN", "100"))
	PRICE_MAX = int(os.getenv("PRICE_MAX", "1000000"))
	REPORT_FILE = os.getenv("REPORT_FILE", "wildberries_report.xlsx")

	async with Parser(
		search_config=SearchConfig(headless=HEADLESS, concurrency=MAX_CONCURRENT_PAGES),
		basket_config=BasketConfig(
			enabled=WITH_BASKET, concurrency=MAX_CONCURRENT_ASYNC_TASKS
		),
	) as parser:
		products = await parser.get_full_products(
			QUERY, PRICE_MIN, PRICE_MAX, MAX_PAGES
		)
		save_to_excel(products, REPORT_FILE)


if __name__ == "__main__":
	asyncio.run(main())
