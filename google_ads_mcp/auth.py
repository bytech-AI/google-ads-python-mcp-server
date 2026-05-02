"""OAuth2 helpers for the Google Ads MCP server.

Refresh token is read from environment variables (Vercel secrets in production).
We exchange it for a short-lived access token on demand.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import httpx

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"

REQUIRED_ENV_VARS = (
    "GOOGLE_ADS_CLIENT_ID",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN",
    "GOOGLE_ADS_DEVELOPER_TOKEN",
)


@dataclass
class AccessToken:
    token: str
    expires_at: float  # epoch seconds


_cached: AccessToken | None = None


def _missing_env() -> list[str]:
    return [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]


async def get_access_token(force_refresh: bool = False) -> AccessToken:
    """Return a cached access token, refreshing it when expired."""
    global _cached

    missing = _missing_env()
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    if not force_refresh and _cached and _cached.expires_at - 60 > time.time():
        return _cached

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            OAUTH_TOKEN_URL,
            data={
                "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
                "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
                "grant_type": "refresh_token",
            },
        )
    response.raise_for_status()
    payload = response.json()

    expires_in = int(payload.get("expires_in", 3600))
    _cached = AccessToken(
        token=payload["access_token"],
        expires_at=time.time() + expires_in,
    )
    return _cached
