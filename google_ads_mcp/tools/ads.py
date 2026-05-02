"""Ad-level tools: get_ad_performance, get_ad_creatives."""

from __future__ import annotations

from google_ads_mcp.client import normalize_customer_id, search_stream
from google_ads_mcp.coordinator import mcp
from google_ads_mcp.tools.gaql import execute_gaql_query


@mcp.tool()
async def get_ad_performance(customer_id: str, days: int = 30) -> str:
    """Return ad performance metrics for the last N days."""
    query = f"""
        SELECT
          ad_group_ad.ad.id,
          ad_group_ad.ad.name,
          ad_group_ad.status,
          campaign.name,
          ad_group.name,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions
        FROM ad_group_ad
        WHERE segments.date DURING LAST_{days}_DAYS
        ORDER BY metrics.impressions DESC
        LIMIT 50
    """
    return await execute_gaql_query(customer_id, query)


@mcp.tool()
async def get_ad_creatives(customer_id: str) -> str:
    """Return ad creative details (RSA headlines/descriptions, final URLs)."""
    query = """
        SELECT
          ad_group_ad.ad.id,
          ad_group_ad.ad.name,
          ad_group_ad.ad.type,
          ad_group_ad.ad.final_urls,
          ad_group_ad.status,
          ad_group_ad.ad.responsive_search_ad.headlines,
          ad_group_ad.ad.responsive_search_ad.descriptions,
          ad_group.name,
          campaign.name
        FROM ad_group_ad
        WHERE ad_group_ad.status != 'REMOVED'
        ORDER BY campaign.name, ad_group.name
        LIMIT 50
    """
    rows = search_stream(customer_id, query)
    if not rows:
        return "この顧客IDの広告クリエイティブが見つかりませんでした。"

    lines = [
        f"顧客ID {normalize_customer_id(customer_id)} の広告クリエイティブ:",
        "=" * 80,
    ]
    for index, row in enumerate(rows, start=1):
        ad_group_ad = row.get("adGroupAd", {}) or {}
        ad = ad_group_ad.get("ad", {}) or {}
        ad_group = row.get("adGroup", {}) or {}
        campaign = row.get("campaign", {}) or {}

        lines.append(f"\n{index}. キャンペーン: {campaign.get('name', 'N/A')}")
        lines.append(f"   広告グループ: {ad_group.get('name', 'N/A')}")
        lines.append(f"   広告ID: {ad.get('id', 'N/A')}")
        lines.append(f"   広告名: {ad.get('name', 'N/A')}")
        lines.append(f"   ステータス: {ad_group_ad.get('status', 'N/A')}")
        lines.append(f"   タイプ: {ad.get('type', 'N/A')}")

        rsa = ad.get("responsiveSearchAd") or {}
        headlines = rsa.get("headlines") or []
        descriptions = rsa.get("descriptions") or []
        if headlines:
            lines.append("   見出し:")
            for h in headlines:
                lines.append(f"     - {h.get('text', 'N/A')}")
        if descriptions:
            lines.append("   説明文:")
            for d in descriptions:
                lines.append(f"     - {d.get('text', 'N/A')}")

        final_urls = ad.get("finalUrls") or []
        if final_urls:
            lines.append(f"   最終URL: {', '.join(final_urls)}")

        lines.append("-" * 80)

    return "\n".join(lines)
