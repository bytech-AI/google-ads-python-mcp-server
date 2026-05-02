"""Account-level tools: list_accounts, get_account_currency."""

from __future__ import annotations

from google_ads_mcp.client import (
    list_accessible_customers,
    normalize_customer_id,
    search_stream,
)
from google_ads_mcp.coordinator import mcp


@mcp.tool()
async def list_accounts() -> str:
    """List every Google Ads account accessible to the configured credentials."""
    resource_names = list_accessible_customers()
    if not resource_names:
        return "アクセス可能なアカウントが見つかりません。"

    lines = ["アクセス可能なGoogle Adsアカウント:", "-" * 50]
    for resource in resource_names:
        customer_id = resource.split("/")[-1]
        lines.append(f"アカウントID: {normalize_customer_id(customer_id)}")
    return "\n".join(lines)


@mcp.tool()
async def get_account_currency(customer_id: str) -> str:
    """Return the default currency code for the given Google Ads account."""
    query = "SELECT customer.id, customer.currency_code FROM customer LIMIT 1"
    rows = search_stream(customer_id, query)
    if not rows:
        return "この顧客IDのアカウント情報が見つかりませんでした。"

    customer = rows[0].get("customer", {}) or {}
    currency = customer.get("currencyCode", "指定なし")
    return f"アカウント {normalize_customer_id(customer_id)} の使用通貨: {currency}"
