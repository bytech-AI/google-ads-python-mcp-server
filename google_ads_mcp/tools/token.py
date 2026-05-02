"""Token utility tools: check_token_validity."""

from __future__ import annotations

import time

from google_ads_mcp.auth import get_access_token
from google_ads_mcp.coordinator import mcp


@mcp.tool()
async def check_token_validity() -> str:
    """Verify that the configured refresh token can mint an access token."""
    header = "=" * 60
    title = "Google Ads アクセストークン有効性チェック"
    try:
        token = await get_access_token()
        remaining = max(0, int(token.expires_at - time.time()))
        hours, rest = divmod(remaining, 3600)
        minutes = rest // 60
        return "\n".join(
            [
                header,
                title,
                header,
                "",
                "✓ トークンは有効です",
                f"残り時間: {hours}時間 {minutes}分",
                "",
                header,
            ]
        )
    except Exception as exc:  # noqa: BLE001
        return "\n".join(
            [
                header,
                title,
                header,
                "",
                "✗ トークンは無効です",
                f"エラー: {exc}",
                "",
                header,
            ]
        )
