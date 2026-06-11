<div align="left">
  <h1>ThesisDefender</h1>
  <p><strong>Paste any argument. Find out exactly where it breaks.</strong></p>
  <p><i>Built for the Microsoft Agents League Hackathon 2026 (Reasoning Agents track)</i></p>
  
  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688.svg)](https://fastapi.tiangolo.com/)
  [![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  ![Vercel](https://img.shields.io/badge/Deployed_on-Vercel-black.svg)
  ![Hugging Face](https://img.shields.io/badge/Backend-Hugging_Face-yellow.svg)

  <h3><a href="https://thesis-defender.vercel.app">🚀 Try the Live Demo</a> | <a href="https://huggingface.co/spaces/SreeNaresh/thesis-defender">🤖 View Backend API</a></h3>
</div>

<hr />

## 📖 Overview

**ThesisDefender** is an adversarial argument reasoning agent designed to stress-test your claims. Unlike debate tools or essay helpers, it doesn't just help you write—it dismantles what you already have and tells you exactly where your reasoning breaks, acting as a crucible for your ideas.

It takes any claim, thesis, or argument as plain text input and deploys a sophisticated, multi-step reasoning agent that:
1. **Steel-Mans**: Builds the strongest possible defense of the argument.
2. **Attacks**: Constructs the most devastating counterargument.
3. **Exposes the Weakest Link**: Identifies the single most fragile assumption in the argument chain.
4. **Strengthens**: Generates a fortified, patched version of the original claim.
5. **Scores**: Assigns an **Argument Resilience Score** (0–100) based on objective analysis.

## 🚀 The Constraint: 3 LLM Calls Maximum

Efficiency and precision are at the core of ThesisDefender. This project adheres to a strict limit of exactly **3 LLM API calls per analysis**:

| Phase | Description |
| :--- | :--- |
| **Call 1 (Structure)** | Extracts the core claim, sub-claims, and implicit assumptions. |
| **Retrieval Pass** | *Not an LLM call.* Uses Microsoft Foundry IQ to fetch real-world evidence based on the structure. |
| **Call 2 (Dual Reasoning)** | Generates both the steel-man defense and strongest attack simultaneously in one pass, utilizing the retrieved evidence. |
| **Call 3 (Verdict)** | Synthesizes the analysis into a Resilience Score, assessment, and actionable improvements. |

## 💻 Tech Stack & Packages

We utilize a modern, highly responsive stack split into a robust asynchronous backend and a sleek frontend.

### Backend (AI & API)
*Powered by Python & FastAPI*
- **`fastapi` & `uvicorn`**: High-performance async REST API framework.
- **`pydantic` v2**: For strict, robust JSON schema validation and serialization.
- **`redis`**: For async job queuing (with silent in-memory fallback for local dev).
- **`openai` & `google-generativeai`**: Native SDKs for model inference.
- **`azure-search-documents` & `azure-identity`**: Microsoft Foundry IQ integration for agentic retrieval.
- **Model Support**: GitHub Models (Default), OpenAI, Gemini, OpenRouter.

### Frontend (UI/UX)
*Powered by Next.js & React*
- **Next.js 14** (App Router): React framework for seamless routing and server-side rendering.
- **React 18**: Component-based UI logic.
- **TailwindCSS**: Utility-first CSS framework for a premium, responsive dark-mode aesthetic.
- **Framer Motion**: For fluid animations, dynamic panel transitions, and the interactive resilience meter.

## 🛠️ Setup & Installation

Get ThesisDefender running locally in minutes.

### 1. Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Environment Configuration:
   Copy `.env.example` to `.env` and configure your keys:
   ```env
   MODEL_PROVIDER=openrouter
   OPENROUTER_API_KEY=your_openrouter_api_key
   # Alternatively: GITHUB_TOKEN, OPENAI_API_KEY, etc.
   ```
4. Start the Server:
   ```bash
   uvicorn main:app --reload
   ```
   *(Optional: Start a Redis instance for durable background jobs)*

### 2. Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Environment Configuration:
   Copy `.env.local.example` to `.env.local` to point to your backend API.
4. Start the Application:
   ```bash
   npm run dev
   ```

## 🌍 Deployment

### Deploy Backend (Hugging Face Spaces)
The backend is Dockerized and pre-configured for Hugging Face Spaces.
1. Create a new **Docker** Space on Hugging Face.
2. Link your GitHub repository or copy the contents of the `backend` folder.
3. In your Space's **Settings**, add the necessary Secrets (e.g., `MODEL_PROVIDER`, `OPENROUTER_API_KEY`).
4. The Space will automatically build and deploy on port `7860`.

### Deploy Frontend (Vercel)
The frontend is built with Next.js and deploys seamlessly on Vercel.
1. Go to your Vercel Dashboard and click **Add New > Project**.
2. Import this GitHub repository.
3. Set the **Framework Preset** to `Next.js` and the **Root Directory** to `frontend`.
4. In the **Environment Variables** section, add:
   - `NEXT_PUBLIC_API_URL`: Set this to your Hugging Face Space URL (e.g., `https://your-username-spacename.hf.space`).
5. Click **Deploy**.

## 🎥 Demonstration

Want to see it in action? Check out our 3-minute hackathon pitch script in [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).

---
<div align="center">
  <i>"ThesisDefender doesn't win your argument for you. It finds the hole in it — before someone else does."</i>
</div>
