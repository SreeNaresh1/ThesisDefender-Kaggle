"""
ThesisDefender MCP Client
==========================
Async client wrapper for calling the ThesisDefender MCP server from
within the ADK agent pipeline. Used by OrchestratorAgent and ProsecutorAgent.

Design principles:
  - Graceful degradation: all methods return None if the server is
    unreachable, so agents continue without enrichment rather than failing.
  - Per-call connections: each tool call opens a fresh SSE connection and
    closes it immediately. Lightweight and stateless.
  - Lazy import: `fastmcp` is imported only inside _call_tool(), so this
    module can be imported even if fastmcp is not installed.

Usage (inside an ADK agent):
  client = ThesisDefenderMCPClient("http://localhost:8001/sse")
  result = await client.verify_claim_type("AI will replace programmers")
  if result:
      attack_vectors = result["typical_attack_vectors"]
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ThesisDefenderMCPClient:
    """
    Async MCP client for the ThesisDefender argument-analysis tools.

    Connects to the FastMCP SSE server and calls tools over the
    Model Context Protocol. All methods are safe to call when the
    server is offline — they return None instead of raising exceptions.

    Args:
        server_url: SSE endpoint of the running MCP server.
                    Default matches mcp_server/run_server.py default port.
    """

    def __init__(self, server_url: str = "http://localhost:8001/sse"):
        self.server_url = server_url

    async def _call_tool(self, tool_name: str, arguments: dict) -> Optional[dict]:
        """
        Open an SSE connection, call a tool, parse the JSON result, close.

        Returns:
            Parsed dict from the tool's JSON response, or None on any error.
        """
        try:
            from fastmcp import Client
            from fastmcp.client.transports import SSETransport

            transport = SSETransport(url=self.server_url)
            async with Client(transport) as client:
                result = await client.call_tool(tool_name, arguments)

            # FastMCP returns a list of content items; first item is the text
            if result and len(result) > 0:
                raw = result[0]
                # result items may be TextContent objects or plain strings
                text = raw.text if hasattr(raw, "text") else str(raw)
                return json.loads(text)

            return None

        except Exception as exc:
            # Server offline, network error, or parse failure — degrade gracefully
            logger.debug(
                "[MCPClient] Tool '%s' call failed (server may be offline): %s",
                tool_name,
                str(exc),
            )
            return None

    # -----------------------------------------------------------------------
    # Public tool methods
    # -----------------------------------------------------------------------

    async def lookup_definition(self, term: str) -> Optional[dict]:
        """
        Look up a logical, rhetorical, or argumentative term.

        Returns:
            dict(term, definition, category, examples, related_terms) or None
        """
        return await self._call_tool("lookup_definition", {"term": term})

    async def verify_claim_type(self, claim_text: str) -> Optional[dict]:
        """
        Identify the logical type of a claim and return targeted attack vectors.

        Returns:
            dict(claim_type, confidence, markers_found,
                 typical_attack_vectors, scrutiny_questions) or None
        """
        return await self._call_tool("verify_claim_type", {"claim_text": claim_text})

    async def explain_research_term(self, term: str) -> Optional[dict]:
        """
        Explain a research methodology or statistical term.

        Returns:
            dict(term, field, explanation,
                 common_misconceptions, example_in_context) or None
        """
        return await self._call_tool("explain_research_term", {"term": term})
