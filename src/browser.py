import asyncio
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class PagePool:
	"""Manages a pool of reusable Playwright pages for concurrent operations."""

	def __init__(self, browser: Browser, context: BrowserContext, size: int):
		"""Initialize the pool with placeholders; pages are created later."""
		self.browser = browser
		self.context = context
		self._pool = asyncio.Queue()
		for _ in range(size):
			self._pool.put_nowait(None)

	async def init_pages(self):
		"""Create and store actual Playwright pages in the pool."""
		for _ in range(self._pool.qsize()):
			page = await self.context.new_page()
			await self._pool.put(page)

	async def get_page(self) -> Page:
		"""Retrieve a page from the pool, creating one if needed."""
		page = await self._pool.get()
		if page is None:
			page = await self.context.new_page()
		return page

	async def release_page(self, page: Page):
		"""Return a page back into the pool."""
		await self._pool.put(page)

	async def close_all(self):
		"""Close all pages stored in the pool."""
		while not self._pool.empty():
			page = await self._pool.get()
			if page:
				await page.close()


class BrowserManager:
	"""Handles Playwright browser lifecycle and manages a page pool."""

	def __init__(self, headless: bool = False, pool_size: int = 5):
		"""Initialize browser settings and pool configuration."""
		self.headless = headless
		self.pool_size = pool_size
		self.playwright = None
		self.browser: Browser | None = None
		self.context: BrowserContext | None = None
		self.pool: PagePool | None = None

	async def start(self):
		"""Launch the browser, create context, initialize page pool."""
		self.playwright = await async_playwright().start()
		self.browser = await self.playwright.chromium.launch(
			headless=self.headless,
			args=[
				"--disable-blink-features=AutomationControlled",
				"--no-sandbox",
				"--lang=ru",
				"--window-size=1920,1080",
			],
		)

		self.context = await self.browser.new_context(
			viewport={"width": 1920, "height": 1080},
			user_agent=(
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
				"AppleWebKit/537.36 (KHTML, like Gecko) "
				"Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
			),
			locale="ru-RU",
			timezone_id="Europe/Moscow",
		)

		self.pool = PagePool(self.browser, self.context, self.pool_size)
		await self.pool.init_pages()

		# Initial warm-up request to pass WB anti-bot checks
		print("Initializing browser and performing warm-up request...")
		page = await self.pool.get_page()
		try:
			await page.goto("https://www.wildberries.ru/")
			await page.wait_for_load_state("domcontentloaded")
			await asyncio.sleep(3)
			print("Warm-up completed.")
		finally:
			await self.pool.release_page(page)

	async def stop(self):
		"""Close all pages, context, browser, and Playwright instance."""
		if self.pool:
			await self.pool.close_all()
		if self.context:
			await self.context.close()
		if self.browser:
			await self.browser.close()
		if self.playwright:
			await self.playwright.stop()
