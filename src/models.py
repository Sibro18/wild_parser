from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PriceData:
	"""Represents price information for a specific product size."""

	basic: int  # Original price in minor currency units (e.g., kopecks)
	product: int  # Discounted or current price in minor currency units


@dataclass
class CardDetails:
	"""Basic product information collected from the search results."""

	url: str  # URL to the product page
	article_id: int  # Unique product identifier
	name: str  # Product name
	price: Dict[str, PriceData]  # Price data per size name
	quantity: int  # Total available stock
	seller_name: str  # Seller display name
	seller_url: str  # URL to the seller's profile
	rating: float  # Average customer rating
	feedbacks_count: int  # Number of customer reviews
	sizes: List[str]  # List of available size labels


@dataclass
class ProductDetails(CardDetails):
	"""Extended product information including description and images."""

	description: Optional[str] = None  # Product description text
	image_urls: Optional[List[str]] = None  # List of product image URLs
