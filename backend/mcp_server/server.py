"""
ThesisDefender MCP Server
==========================
A FastMCP server that exposes three argument-analysis tools to any
MCP-compatible client (including Google ADK agents).

Server: ThesisDefender
Transport: SSE (HTTP)
Default port: 8001 (override with MCP_PORT env var)

Tools
-----
  lookup_definition(term)          → LogicDefinition
  verify_claim_type(claim_text)    → ClaimTypeAnalysis
  explain_research_term(term)      → ResearchTermExplanation

Starting the server
-------------------
  cd backend/
  python -m mcp_server.run_server

  # Or with custom port:
  MCP_PORT=9000 python -m mcp_server.run_server

Calling from an ADK agent (via mcp_server/client.py)
-----------------------------------------------------
  from mcp_server.client import ThesisDefenderMCPClient
  client = ThesisDefenderMCPClient("http://localhost:8001/sse")
  result = await client.verify_claim_type("AI will replace all programmers")
"""

from fastmcp import FastMCP

from mcp_server.tools import (
    run_lookup_definition,
    run_verify_claim_type,
    run_explain_research_term,
)

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="ThesisDefender",
    instructions=(
        "Argument analysis enrichment tools for the ThesisDefender adversarial "
        "reasoning pipeline. Use these tools to enrich agent prompts with "
        "targeted attack vectors, precise term definitions, and research methodology "
        "explanations."
    ),
)


# ---------------------------------------------------------------------------
# Tool 1: Definition Lookup
# ---------------------------------------------------------------------------

@mcp.tool()
def lookup_definition(term: str) -> dict:
    """
    Look up the precise definition of a logical, rhetorical, or argumentative term.

    Returns the definition, category, concrete examples, and related terms.
    Use this tool when an argument invokes specific reasoning concepts
    (e.g., 'steel man', 'ad hominem', 'slippery slope', 'post hoc').

    Args:
        term: The term to look up. Case-insensitive.
               Examples: 'steel man', 'confirmation bias', 'modus ponens'

    Returns:
        A dict with: term, definition, category, examples, related_terms
    """
    return run_lookup_definition(term)


# ---------------------------------------------------------------------------
# Tool 2: Claim Type Verification
# ---------------------------------------------------------------------------

@mcp.tool()
def verify_claim_type(claim_text: str) -> dict:
    """
    Identify the logical type of a claim and return targeted attack vectors.

    Analyses the claim text for linguistic markers to classify it as:
    factual, predictive, causal, ethical, policy, or subjective.

    Returns the claim type, confidence score, matched markers, and a
    curated list of the most effective attack vectors for that claim type.
    Use this tool to give the Prosecutor agent more precise, targeted angles.

    Args:
        claim_text: The main claim to analyse (the 'main_claim' field from
                    the ArgumentStructure). Limit to 500 characters.

    Returns:
        A dict with: claim_type, confidence, markers_found,
                     typical_attack_vectors, scrutiny_questions, claim_preview
    """
    return run_verify_claim_type(claim_text[:500])


# ---------------------------------------------------------------------------
# Tool 3: Research Term Explanation
# ---------------------------------------------------------------------------

@mcp.tool()
def explain_research_term(term: str) -> dict:
    """
    Explain a research methodology or statistical term referenced in an argument.

    Covers: peer review, meta-analysis, randomized controlled trial, p-value,
    statistical significance, effect size, confidence interval, observational study,
    null hypothesis, selection bias, replication crisis, external validity, and more.

    Use this tool when an argument cites research, statistics, or studies,
    to understand the precise meaning and common misconceptions of the cited methods.

    Args:
        term: The research or statistical term to explain. Case-insensitive.
               Examples: 'p-value', 'meta-analysis', 'selection bias'

    Returns:
        A dict with: term, field, explanation, common_misconceptions, example_in_context
    """
    return run_explain_research_term(term)
