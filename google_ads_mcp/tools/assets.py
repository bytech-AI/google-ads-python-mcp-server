"""Asset-level tools: get_image_assets."""

from __future__ import annotations

from google_ads_mcp.client import normalize_customer_id, search_stream
from google_ads_mcp.coordinator import mcp


@mcp.tool()
async def get_image_assets(customer_id: str, limit: int = 50) -> str:
    """List image assets uploaded to the account."""
    query = f"""
        SELECT
          asset.id,
          asset.name,
          asset.type,
          asset.image_asset.full_size.url,
          asset.image_asset.full_size.height_pixels,
          asset.image_asset.full_size.width_pixels,
          asset.image_asset.file_size
        FROM asset
        WHERE asset.type = 'IMAGE'
        LIMIT {limit}
    """
    rows = search_stream(customer_id, query)
    if not rows:
        return "この顧客IDの画像アセットが見つかりませんでした。"

    lines = [
        f"顧客ID {normalize_customer_id(customer_id)} の画像アセット:",
        "=" * 80,
    ]
    for index, row in enumerate(rows, start=1):
        asset = row.get("asset", {}) or {}
        image_asset = asset.get("imageAsset", {}) or {}
        full_size = image_asset.get("fullSize", {}) or {}

        lines.append(f"\n{index}. アセットID: {asset.get('id', 'N/A')}")
        lines.append(f"   名前: {asset.get('name', 'N/A')}")
        if full_size:
            lines.append(f"   画像URL: {full_size.get('url', 'N/A')}")
            lines.append(
                f"   サイズ: {full_size.get('widthPixels', 'N/A')} x "
                f"{full_size.get('heightPixels', 'N/A')} px"
            )
        file_size = image_asset.get("fileSize")
        if file_size:
            try:
                lines.append(f"   ファイルサイズ: {int(file_size) / 1024:.2f} KB")
            except (TypeError, ValueError):
                pass
        lines.append("-" * 80)

    return "\n".join(lines)
