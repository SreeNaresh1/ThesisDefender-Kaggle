# ThesisDefender

**Paste any argument. Find out where it breaks.**

Built for the Microsoft Agents League Hackathon 2026 (Reasoning Agents track).

ThesisDefender is an adversarial argument reasoning agent. Unlike debate tools or essay helpers, it doesn't help you write \u2014 it stress-tests what you already have and tells you exactly where your reasoning breaks.

It takes any claim, thesis, or argument as plain text input and deploys a multi-step reasoning agent that:
1. Builds the strongest possible defense of the argument (steel-man)
2. Constructs the most devastating counterargument (attack)
3. Identifies the single weakest link in the argument chain
4. Generates a strengthened version of the original claim
5. Assigns an Argument Resilience Score (0\u2013100)

## The Constraint: 3 LLM Calls Maximum

This project adheres to a strict limit of exactly **3 LLM API calls per analysis**.

1. **Call 1 (Structure):** Extracts the core claim, sub-claims, and implicit assumptions.
2. **Retrieval (Not an LLM call):** Uses Microsoft Foundry IQ to fetch real-world evidence based on the structure.
3. **Call 2 (Dual Reasoning):** Generates both the steel-man defense and strongest attack simultaneously in one pass, utilizing the retrieved evidence.
4. **Call 3 (Verdict):** Synthesizes the analysis into a Resilience Score, assessment, and actionable improvements.

## Tech Stack

### Backend
- **Python 3.11+**, **FastAPI (async)**
- **Azure AI Foundry** (Project hub, Foundry IQ for retrieval)
- **Pydantic v2** for robust JSON validation
- **Redis** for async job queuing (with silent in-memory fallback)
- **Model Support:** GitHub Models (Default), OpenAI, Gemini

### Frontend
- **Next.js 14** (App Router)
- **React 18**
- **TailwindCSS** for dark-mode premium styling
- **Framer Motion** for fluid resilience meter and panel animations

## Setup & Installation

### Backend Setup
1. Navigate to the `backend` directory.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your API keys:
   - `MODEL_PROVIDER=github`
   - `GITHUB_TOKEN=your_token`
   - Set Azure Search credentials for Foundry IQ if available.
4. Run the API: `uvicorn main:app --reload`
   *(Optional: Start a Redis instance for durable background jobs)*

### Frontend Setup
1. Navigate to the `frontend` directory.
2. Install dependencies: `npm install`
3. Copy `.env.local.example` to `.env.local`.
4. Run the development server: `npm run dev`

## Demonstration
See `DEMO_SCRIPT.md` for our 3-minute hackathon pitch script.
