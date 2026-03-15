from json import loads
from typing import Any, Optional
from playwright.async_api import Page, Response


async def safe_json(response: Response) -> Optional[Any]:
	"""Safely attempt to parse JSON from a Playwright response."""
	try:
		return await response.json()
	except Exception:
		return None


async def safe_text(response: Response) -> Optional[str]:
	try:
		return await response.text()
	except Exception:
		return None


def safe_parse_json(text: str) -> Optional[Any]:
	try:
		return loads(text)
	except Exception:
		return None


async def safe_pre(page: Page) -> Optional[str]:
	try:
		return await page.text_content("pre", timeout=2000)
	except Exception:
		return None
