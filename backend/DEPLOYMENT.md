# ThesisDefender Deployment Guide

This document outlines the deployment architecture for ThesisDefender following the Kaggle Capstone upgrades (Google ADK, FastMCP). The architecture preserves the original simple deployment flows.

## 1. Backend: Hugging Face Spaces (Docker)

The backend is deployed as a single Docker container on Hugging Face Spaces. It runs both the FastAPI backend and the new FastMCP server.

### Architecture

- **Base Image:** `python:3.11-slim`
- **Exposed Port:** `7860` (Hugging Face standard)
- **Startup Script:** `start.sh`

In Phase 5, we migrated from running `uvicorn` directly to using `start.sh`. This script launches two processes:
1. `python -m mcp_server.run_server &` (runs the FastMCP server in the background on port `8001`).
2. `uvicorn main:app --host 0.0.0.0 --port 7860` (runs the FastAPI backend in the foreground).

Because they share the same container network, the ADK `OrchestratorAgent` can seamlessly connect to the MCP Server at `http://localhost:8001/sse`. No external routing or multi-container setup is required.

### Required Environment Variables
Configure these in the Hugging Face Spaces Settings -> Secrets:
- `MODEL_PROVIDER`: Set to your preferred provider (e.g., `openai`, `gemini`, `github`)
- `<PROVIDER_API_KEY>`: e.g., `OPENAI_API_KEY`, `GEMINI_API_KEY`
- `REDIS_URL`: (Optional) URL of your Redis instance. If omitted, the application will degrade gracefully to an in-memory queue.
- `USE_ADK`: `true` (enables the new multi-agent pipeline)
- `MCP_SERVER_URL`: `http://localhost:8001/sse` (the internal URL where FastAPI finds the MCP server)

---

## 2. Frontend: Vercel

The Next.js frontend remains completely unchanged and isolated from backend architectural shifts.

### Deployment Flow
1. Connect your GitHub repository to Vercel.
2. Select the `frontend` directory as the Root Directory in Vercel settings.
3. Framework Preset: Next.js
4. Build Command: `npm run build`
5. Install Command: `npm install`

### Required Environment Variables
Configure these in Vercel Settings -> Environment Variables:
- `NEXT_PUBLIC_API_URL`: The URL of your Hugging Face Space (e.g., `https://your-username-thesisdefender.hf.space`)

---

## 3. Local Development (Docker Compose)

For local development, `docker-compose.yml` provides a self-contained environment with Redis.

```bash
cd backend
docker-compose up --build
```
This builds the Dockerfile, runs `start.sh`, and maps ports `7860` (FastAPI) and `8001` (FastMCP) to your host machine.

---

## 4. Dependencies Map

The `backend/requirements.txt` was updated with the following core packages:

- **Web & Core:** `fastapi==0.111.0`, `uvicorn==0.30.1`, `pydantic>=2.9.0`
- **Agents (Phase 1):** `google-adk>=1.0.0` (Powers the `SequentialAgent` pipeline)
- **MCP Tools (Phase 2):** `fastmcp>=2.0.0` (Standalone package to run the Server and SSE Client)
- **LLM Clients:** `openai`, `google-generativeai`

No new binary dependencies, system packages, or external databases were introduced, ensuring the `Dockerfile` remains lightweight.
