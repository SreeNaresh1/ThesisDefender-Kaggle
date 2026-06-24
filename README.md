---
title: ThesisDefender
emoji: 🛡️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---
<div align="left">
  <h1>ThesisDefender — Kaggle AI Agents Capstone</h1>
  <p><strong>Paste any argument. Find out exactly where it breaks.</strong></p>
  <p>🌍 <strong>Live Demo:</strong> <a href="https://thesis-defender-kaggle.vercel.app">thesis-defender-kaggle.vercel.app</a></p>
  
  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688.svg)](https://fastapi.tiangolo.com/)
  [![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
</div>

<hr />

## 📖 Problem Statement

In an era of rapid information generation, humans struggle to rigorously stress-test their own claims. Confirmation bias prevents authors from seeing structural flaws in their arguments. We need an automated, adversarial system that doesn't just help you write, but intentionally dismantles your reasoning to expose hidden assumptions, logical fallacies, and structural weaknesses before publication.

## 🤖 Why Agents?

A single LLM prompt cannot effectively steel-man an argument and simultaneously destroy it without suffering from context confusion and hallucination. By employing a multi-agent system, we separate concerns:
1. **Orchestrator** extracts neutral facts.
2. **Defense Counsel** is heavily biased toward proving the claim.
3. **Prosecutor** is ruthlessly incentivized to destroy the defense.
4. **Judge** remains objective, scoring the aftermath.

This adversarial framework mathematically forces the LLM out of its helpful "yes-man" default and produces a genuinely critical analysis.

## 🏛️ Architecture

ThesisDefender uses a decoupled, modern architecture:
- **Backend:** Python + FastAPI for asynchronous job handling.
- **Frontend:** Next.js 14 + TailwindCSS for a highly responsive, animated UI.
- **Job Queue:** Redis-backed queue (with an in-memory fallback) for long-running reasoning tasks.
- **Model Inference:** Abstracted `ModelClient` supporting GitHub Models, OpenAI, Gemini, and OpenRouter.

## 🧬 ADK Design

We leverage the **Google Agent Development Kit (ADK)** to orchestrate the workflow.
We implemented a `SequentialAgent` pipeline where state is passed continuously via `InvocationContext.session.state`.

**Pipeline Flow:**
1. `OrchestratorAgent`: Extracts the core claim and assumptions.
2. `DefenseCounselAgent`: Steel-mans the argument.
3. `ProsecutorAgent`: Reads the defense and constructs a targeted attack.
4. `JudgeAgent`: Synthesizes the debate into a 0-100 Resilience Score and actionable fixes.

## 🔌 MCP Integration

To ground the Prosecutor Agent and avoid hallucinations, we implemented a **Model Context Protocol (FastMCP)** Server.
- The `OrchestratorAgent` invokes the MCP server (`verify_claim_type`) to classify the argument (e.g., "Predictive", "Causal").
- The MCP server returns purely deterministic, expert-curated attack vectors.
- These vectors are injected directly into the `ProsecutorAgent`'s context, resulting in highly precise counterarguments (e.g., attacking correlation vs. causation for Causal claims).

## 🔒 Security Features

Security is implemented as a 4-layer standalone module:
1. **Input Validation:** Enforces strict length limits, printability ratios, and strips C0 control characters.
2. **Prompt Injection Guard:** 17 regex patterns catch jailbreaks (DAN), system prompt exfiltration, and instruction overrides.
3. **Secrets Audit:** Warns on startup if API keys are missing, hardcoded, or using placeholder values.
4. **Structured Output Validation:** Business logic guards (e.g., ensuring a Resilience Score of 15 isn't labeled "Robust").

## 💻 CLI Usage

ThesisDefender includes an Agent Skills CLI that runs the exact same ADK pipeline locally without starting a web server.

```bash
# Analyze inline text
thesis-defender analyze --input "AI will replace all programmers by 2030."

# Analyze a file
thesis-defender analyze examples/claim.md
```
The CLI renders a rich terminal report and automatically saves the structured result as a JSON artifact.

## 🚀 Deployment

- **Backend (Hugging Face Spaces):** A single Docker container running both the FastAPI backend (`7860`) and the FastMCP server (`8001`) simultaneously via `start.sh`.
- **Frontend (Vercel):** Deployed as a serverless Next.js application, pointing to the Hugging Face Space API URL.



## 🔮 Future Improvements

- **Web Search Tools:** Allow the MCP server to fetch real-time citations.
- **Streaming UI:** Stream the internal monologues of the Defense and Prosecutor agents to the frontend in real-time.
- **Custom Personas:** Allow users to define the "Prosecutor" (e.g., "Argue from a purely economic standpoint").

## 🔑 Environment Variables

```env
# Core Backend Settings
MODEL_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Agent Features
USE_ADK=true
MCP_SERVER_URL=http://localhost:8001/sse
```

## 🛠️ Setup Guide

**Backend Setup:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
uvicorn main:app --reload
```
*(Alternatively, run the MCP server in a separate terminal: `python -m mcp_server.run_server`)*

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
```

## 🔄 Development Workflow

The backend uses Pytest. Run the security suite and pipeline mocks:
```bash
cd backend
pytest tests/
```

---

# 🎯 Kaggle Evaluation Mapping

To assist judges in evaluating this Capstone submission, the required criteria map to the following implementation locations in the repository:

### 1. ADK Multi-Agent System
- **Location:** [`backend/adk/agents.py`](backend/adk/agents.py) and [`backend/adk/pipeline_adk.py`](backend/adk/pipeline_adk.py)
- **Details:** Implements `google-adk` `BaseAgent` subclasses for Orchestrator, Defense, Prosecutor, and Judge. Uses `SequentialAgent` for stateful orchestration.

### 2. MCP Server Integration
- **Location:** [`backend/mcp_server/server.py`](backend/mcp_server/server.py) and [`backend/mcp_server/tools.py`](backend/mcp_server/tools.py)
- **Details:** A FastMCP server exposing three tools. Wired into the ADK agents via `backend/mcp_server/client.py` using SSE Transport.

### 3. Security Features
- **Location:** [`backend/security/guards.py`](backend/security/guards.py)
- **Details:** Comprehensive 4-layer module including Prompt Injection detection (17 patterns), Input Sanitization, Output Business Validation, and Secrets Auditing. Fully unit-tested in `backend/tests/test_security.py`.

### 4. Deployability
- **Location:** [`backend/Dockerfile`](backend/Dockerfile), [`backend/start.sh`](backend/start.sh), and [`backend/DEPLOYMENT.md`](backend/DEPLOYMENT.md)
- **Details:** Demonstrates Hugging Face Spaces compatibility via a multi-process Docker setup that runs both the MCP Server and the FastAPI web server seamlessly.

### 5. Agent Skills CLI
- **Location:** [`backend/cli/main.py`](backend/cli/main.py) and wrappers (`thesis-defender.cmd`, `thesis-defender`)
- **Details:** A full-featured CLI reusing the exact ADK pipeline logic, featuring a custom terminal output formatter (`backend/cli/formatter.py`) and result saving.
