#!/usr/bin/env python3
"""Vercel API endpoint for the Google Ads MCP server.

Exposes the MCP tools defined in `google_ads_mcp/` over HTTP using JSON-RPC,
compatible with the Streamable HTTP transport (POST /mcp).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from google_ads_mcp.auth import get_access_token
from google_ads_mcp.tools.accounts import get_account_currency, list_accounts
from google_ads_mcp.tools.ads import get_ad_creatives, get_ad_performance
from google_ads_mcp.tools.assets import get_image_assets
from google_ads_mcp.tools.campaigns import get_campaign_performance
from google_ads_mcp.tools.gaql import execute_gaql_query, run_gaql
from google_ads_mcp.tools.token import check_token_validity

logger = logging.getLogger(__name__)

app = FastAPI(title="Google Ads MCP Server", version="1.0.0")

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "MCP-Protocol-Version",
        "Mcp-Session-Id",
    ],
)


def _is_authorized(request: Request) -> bool:
    expected_token = os.getenv("MCP_AUTH_TOKEN")
    if not expected_token:
        return os.getenv("ALLOW_UNAUTHENTICATED_MCP", "").lower() == "true"

    auth_header = request.headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    api_key = request.headers.get("x-api-key", "").strip()
    return token == expected_token or api_key == expected_token


def _origin_is_allowed(request: Request) -> bool:
    origin = request.headers.get("origin")
    if not origin:
        return True
    return origin in ALLOWED_ORIGINS


def _jsonrpc_error(request_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _tool_result(result: Any) -> Dict[str, Any]:
    if not isinstance(result, str):
        result = json.dumps(result, ensure_ascii=False)
    return {"content": [{"type": "text", "text": result}]}


# ------------------------------------------------------------------ #
# Tool registry exposed via tools/list
# ------------------------------------------------------------------ #

_CUSTOMER_ID_FIELD = {
    "type": "string",
    "description": "Google Ads 顧客ID（10桁、ハイフン有無は問わない）。",
}

_TOOLS = [
    {
        "name": "list_accounts",
        "description": "認証済み資格情報でアクセス可能な全 Google Ads アカウントを一覧表示します。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "execute_gaql_query",
        "description": "任意の GAQL クエリを実行し、結果をテーブル形式で返します。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": _CUSTOMER_ID_FIELD,
                "query": {"type": "string", "description": "実行する GAQL クエリ。"},
            },
            "required": ["customer_id", "query"],
        },
    },
    {
        "name": "run_gaql",
        "description": "GAQL クエリをフォーマット指定（table / json / csv）付きで実行します。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": _CUSTOMER_ID_FIELD,
                "query": {"type": "string"},
                "format": {
                    "type": "string",
                    "enum": ["table", "json", "csv"],
                    "default": "table",
                },
            },
            "required": ["customer_id", "query"],
        },
    },
    {
        "name": "get_campaign_performance",
        "description": "直近 N 日間のキャンペーンパフォーマンス指標を返します。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": _CUSTOMER_ID_FIELD,
                "days": {"type": "integer", "default": 30, "minimum": 1},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_ad_performance",
        "description": "直近 N 日間の広告パフォーマンス指標を返します。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": _CUSTOMER_ID_FIELD,
                "days": {"type": "integer", "default": 30, "minimum": 1},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_ad_creatives",
        "description": "広告クリエイティブの詳細（RSA見出し・説明文・最終URL）を返します。",
        "inputSchema": {
            "type": "object",
            "properties": {"customer_id": _CUSTOMER_ID_FIELD},
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_account_currency",
        "description": "アカウントの既定通貨コードを返します。",
        "inputSchema": {
            "type": "object",
            "properties": {"customer_id": _CUSTOMER_ID_FIELD},
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_image_assets",
        "description": "アカウントの画像アセット一覧を返します。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": _CUSTOMER_ID_FIELD,
                "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 500},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "check_token_validity",
        "description": "リフレッシュトークンからアクセストークンを発行できるか確認します。",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


# ------------------------------------------------------------------ #
# Endpoints
# ------------------------------------------------------------------ #


@app.get("/mcp")
async def mcp_stream_not_supported():
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="SSE stream is not supported. Use POST with application/json.",
    )


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    request_id: Any = None

    if not _origin_is_allowed(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Origin not allowed"
        )

    if not _is_authorized(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    try:
        data = await request.json()
        if not isinstance(data, dict):
            return _jsonrpc_error(None, -32600, "Invalid Request")

        method = data.get("method")
        params = data.get("params", {}) or {}
        request_id = data.get("id")
        logger.info("MCP method=%s id_present=%s", method, request_id is not None)

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {"listChanged": True}},
                    "serverInfo": {
                        "name": "Google Ads MCP Server",
                        "version": "1.0.0",
                    },
                },
            }

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": _TOOLS},
            }

        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {}) or {}
            if not isinstance(tool_args, dict):
                return _jsonrpc_error(
                    request_id, -32602, "Tool arguments must be an object"
                )

            dispatch = {
                "list_accounts": list_accounts,
                "execute_gaql_query": execute_gaql_query,
                "run_gaql": run_gaql,
                "get_campaign_performance": get_campaign_performance,
                "get_ad_performance": get_ad_performance,
                "get_ad_creatives": get_ad_creatives,
                "get_account_currency": get_account_currency,
                "get_image_assets": get_image_assets,
                "check_token_validity": check_token_validity,
            }

            handler = dispatch.get(tool_name)
            if handler is None:
                return _jsonrpc_error(request_id, -32601, f"Unknown tool: {tool_name}")

            try:
                result = await handler(**tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": _tool_result(result),
                }
            except TypeError as exc:
                return _jsonrpc_error(request_id, -32602, f"Invalid arguments: {exc}")
            except Exception as exc:  # noqa: BLE001
                logger.exception("Tool execution failed: %s", tool_name)
                return _jsonrpc_error(
                    request_id, -32603, f"Tool execution failed: {exc}"
                )

        return _jsonrpc_error(request_id, -32601, f"Method '{method}' not found")

    except json.JSONDecodeError:
        return _jsonrpc_error(None, -32700, "Parse error")
    except Exception:
        logger.exception("Error processing MCP request")
        return _jsonrpc_error(request_id, -32603, "Internal error")


@app.get("/")
async def root():
    return {
        "name": "Google Ads MCP Server",
        "version": "1.0.0",
        "description": "Remote MCP server for Google Ads (Vercel + FastMCP)",
        "endpoints": {"mcp": "/mcp", "health": "/health"},
    }


@app.get("/health")
async def health_check():
    auth_ok = False
    try:
        await get_access_token()
        auth_ok = True
    except Exception:
        auth_ok = False

    return {
        "status": "healthy" if auth_ok else "unhealthy",
        "service": "Google Ads MCP Server",
        "google_ads_auth_ok": auth_ok,
        "mcp_auth_configured": bool(os.getenv("MCP_AUTH_TOKEN")),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.mcp:app", host="0.0.0.0", port=8000, reload=True)
