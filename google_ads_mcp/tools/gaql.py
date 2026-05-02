"""GAQL execution tools: execute_gaql_query, run_gaql."""

from __future__ import annotations

import json
from typing import Any

from google_ads_mcp.client import (
    collect_field_paths,
    get_field,
    normalize_customer_id,
    search_stream,
)
from google_ads_mcp.coordinator import mcp


def _format_table(rows: list[dict[str, Any]], customer_id: str) -> str:
    fields = collect_field_paths(rows)
    widths = {f: len(f) for f in fields}
    for row in rows:
        for f in fields:
            widths[f] = max(widths[f], len(str(get_field(row, f))))

    lines = [f"アカウント {customer_id} のクエリ結果:", "-" * 100]
    header = " | ".join(f.ljust(widths[f]) for f in fields)
    lines.append(header)
    lines.append("-" * len(header))
    for row in rows:
        lines.append(" | ".join(str(get_field(row, f)).ljust(widths[f]) for f in fields))
    return "\n".join(lines)


def _format_csv(rows: list[dict[str, Any]]) -> str:
    fields = collect_field_paths(rows)
    out = [",".join(fields)]
    for row in rows:
        out.append(
            ",".join(str(get_field(row, f)).replace(",", ";") for f in fields)
        )
    return "\n".join(out)


@mcp.tool()
async def execute_gaql_query(customer_id: str, query: str) -> str:
    """Run an arbitrary GAQL query against the given customer account."""
    rows = search_stream(customer_id, query)
    if not rows:
        return "クエリの結果が見つかりませんでした。"
    return _format_table(rows, normalize_customer_id(customer_id))


@mcp.tool()
async def run_gaql(customer_id: str, query: str, format: str = "table") -> str:
    """Run a GAQL query and format the result as table | json | csv."""
    rows = search_stream(customer_id, query)
    if not rows:
        return "クエリの結果が見つかりませんでした。"

    fmt = (format or "table").lower()
    if fmt == "json":
        return json.dumps({"results": rows}, ensure_ascii=False, indent=2)
    if fmt == "csv":
        return _format_csv(rows)
    return _format_table(rows, normalize_customer_id(customer_id))
