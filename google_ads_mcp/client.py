"""Thin wrapper around the official google-ads SDK.

The SDK is configured purely from environment variables so the same code path
works for stdio (local), uvicorn, and Vercel deployments.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Any, Iterable

from google.ads.googleads.client import GoogleAdsClient


def normalize_customer_id(customer_id: str | int) -> str:
    """Strip non-digits and zero-pad to 10 characters (matching TS impl)."""
    digits = re.sub(r"\D", "", str(customer_id))
    return digits.zfill(10)


def _config_from_env() -> dict[str, Any]:
    config: dict[str, Any] = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if login_customer_id:
        config["login_customer_id"] = normalize_customer_id(login_customer_id)
    return config


@lru_cache(maxsize=1)
def get_client() -> GoogleAdsClient:
    """Build a process-wide GoogleAdsClient from environment variables."""
    return GoogleAdsClient.load_from_dict(_config_from_env())


def search_stream(customer_id: str, query: str) -> list[dict[str, Any]]:
    """Run a GAQL query and return rows as plain dicts (proto-plus → dict)."""
    client = get_client()
    service = client.get_service("GoogleAdsService")
    response = service.search_stream(
        customer_id=normalize_customer_id(customer_id),
        query=query,
    )
    rows: list[dict[str, Any]] = []
    for batch in response:
        for row in batch.results:
            rows.append(_row_to_dict(row))
    return rows


def list_accessible_customers() -> list[str]:
    client = get_client()
    service = client.get_service("CustomerService")
    response = service.list_accessible_customers()
    return list(response.resource_names)


def _row_to_dict(row: Any) -> dict[str, Any]:
    """Convert a proto-plus GoogleAdsRow into a plain JSON-safe dict."""
    from google.protobuf.json_format import MessageToDict

    # proto-plus messages expose `_pb` for the underlying protobuf.
    pb = getattr(row, "_pb", row)
    return MessageToDict(pb, preserving_proto_field_name=False)


def collect_field_paths(rows: Iterable[dict[str, Any]]) -> list[str]:
    """Flatten the first row into dotted field paths (depth 2)."""
    fields: list[str] = []
    for row in rows:
        for key, value in row.items():
            if isinstance(value, dict):
                for sub in value.keys():
                    fields.append(f"{key}.{sub}")
            else:
                fields.append(key)
        break
    return fields


def get_field(row: dict[str, Any], path: str) -> Any:
    if "." in path:
        head, tail = path.split(".", 1)
        sub = row.get(head)
        if isinstance(sub, dict):
            return sub.get(tail, "")
        return ""
    return row.get(path, "")
