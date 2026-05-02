"""Entry point for stdio transport (local development & MCP Inspector).

Importing the tool modules triggers `@mcp.tool()` registration on the shared
FastMCP instance defined in `coordinator.py`.
"""

from google_ads_mcp.coordinator import mcp

# noqa: F401 — imports are required to register tools as side effects
from google_ads_mcp.tools import accounts  # noqa: F401
from google_ads_mcp.tools import ads  # noqa: F401
from google_ads_mcp.tools import assets  # noqa: F401
from google_ads_mcp.tools import campaigns  # noqa: F401
from google_ads_mcp.tools import gaql  # noqa: F401
from google_ads_mcp.tools import token  # noqa: F401


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
