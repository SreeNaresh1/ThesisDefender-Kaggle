"""
ThesisDefender MCP Server — Entry Point
=========================================
Run with:
  cd backend/
  python -m mcp_server.run_server

  # Override port (default: 8001):
  MCP_PORT=9000 python -m mcp_server.run_server

The server starts a FastMCP SSE endpoint.
  SSE stream: http://localhost:8001/sse
  Health:     http://localhost:8001/

Once running, any MCP-compatible client can connect. For ThesisDefender,
the ADK agents connect via mcp_server/client.py using ThesisDefenderMCPClient.

Press Ctrl+C to stop.
"""

import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    from mcp_server.server import mcp

    port = int(os.environ.get("MCP_PORT", "8001"))
    host = os.environ.get("MCP_HOST", "0.0.0.0")

    logger.info("=" * 60)
    logger.info("ThesisDefender MCP Server")
    logger.info("Transport : SSE (HTTP)")
    logger.info("Host      : %s", host)
    logger.info("Port      : %d", port)
    logger.info("SSE URL   : http://%s:%d/sse", host, port)
    logger.info("Tools     : lookup_definition | verify_claim_type | explain_research_term")
    logger.info("=" * 60)

    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()
