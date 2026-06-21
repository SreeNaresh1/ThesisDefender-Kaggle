#!/bin/bash
set -e

echo "Starting ThesisDefender MCP Server in the background..."
export MCP_HOST="0.0.0.0"
export MCP_PORT="8001"
python -m mcp_server.run_server &

echo "Starting FastAPI Application..."
exec uvicorn main:app --host 0.0.0.0 --port 7860
