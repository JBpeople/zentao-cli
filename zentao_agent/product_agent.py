from __future__ import annotations

from dataclasses import asdict
from typing import Any

from google.adk.agents import LlmAgent

from zentao_agent.model import zentao_model
from zentao_cli.auth import client_from_profile
from zentao_cli.errors import ZentaoCliError
from zentao_cli.models import Product


def _product_payload(product: Product) -> dict[str, Any]:
    return asdict(product)


def list_products(page: int = 1, page_size: int = 100, fetch_all: bool = False) -> dict[str, Any]:
    """List Zentao products visible to the current user."""
    try:
        client = client_from_profile()
        products = client.list_products(page=page, page_size=page_size, fetch_all=fetch_all)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"products": [_product_payload(product) for product in products]}


def get_product(product_id: int) -> dict[str, Any]:
    """Get one Zentao product by id."""
    try:
        client = client_from_profile()
        product = client.get_product(product_id)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"product": _product_payload(product)}


product_agent = LlmAgent(
    model=zentao_model(),
    name="product_agent",
    description="Handles read-only Zentao product discovery workflows.",
    instruction=(
        "You are the Zentao product specialist. Handle only read-only product "
        "queries: list visible products and inspect a single product. "
        "Use the provided tools for all product data. If the user asks for "
        "execution, task, story, or bug data, explain that another specialist "
        "should handle that part."
    ),
    tools=[list_products, get_product],
)
