"""Campaign-level tools: get_campaign_performance."""

from __future__ import annotations

from google_ads_mcp.coordinator import mcp
from google_ads_mcp.tools.gaql import execute_gaql_query


@mcp.tool()
async def get_campaign_performance(customer_id: str, days: int = 30) -> str:
    """Return campaign performance metrics for the last N days."""
    query = f"""
        SELECT
          campaign.id,
          campaign.name,
          campaign.status,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.average_cpc
        FROM campaign
        WHERE segments.date DURING LAST_{days}_DAYS
        ORDER BY metrics.cost_micros DESC
        LIMIT 50
    """
    return await execute_gaql_query(customer_id, query)
