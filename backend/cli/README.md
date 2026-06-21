# ThesisDefender CLI 🚀

The ThesisDefender CLI provides a local, terminal-native way to run the full adversarial argument analysis pipeline. 

It executes the **exact same ADK workflow and LLM agents** as the FastAPI server, but runs completely locally without requiring Docker, Redis, or a running web server. The output is printed as a rich terminal report and automatically saved as a JSON artifact.

## Installation Guide

The CLI is already integrated into the repository. You just need to install the backend Python dependencies.

1. **Install Dependencies**
   Navigate to the `backend/` directory and install the requirements:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Ensure you have a `.env` file in the `backend/` directory with your chosen model provider and API key. 
   ```env
   # backend/.env
   MODEL_PROVIDER=github
   GITHUB_TOKEN=ghp_your_token_here
   
   # Optional: Enable MCP Enrichment
   USE_ADK=true
   MCP_SERVER_URL=http://localhost:8001/sse
   ```

3. **Run the Wrappers**
   From the repository root, you can use the provided wrappers for your OS:
   - **Windows:** `thesis-defender.cmd`
   - **Mac/Linux:** `./thesis-defender`

*(If you are already inside the `backend/` directory, you can also run `python -m cli.main analyze ...`)*

---

## Example Commands

You can provide the argument either as an inline string or by pointing to a file.

**Analyze an inline claim:**
```bash
thesis-defender analyze --input "AI will replace all programmers by 2030."
```

**Analyze a Markdown or text file:**
```bash
thesis-defender analyze examples/claim.md
```

**Analyze a file on Windows:**
```cmd
thesis-defender.cmd analyze thesis.txt
```

---

## Example Outputs

### 1. Live Progress
As the agents work, the CLI prints live progress:
```text
🚀 Starting ThesisDefender Analysis (Job: cli_a1b2c3d4)
🤖 Provider: GITHUB
🔄 Engine:   ADK Pipeline (mcp enabled)

  🔍 Step 1/4  Orchestrator: Extracting claim and assumptions...
  🛡️  Step 2/4  Defense Counsel: Building the strongest case...
  ⚔️  Step 3/4  Prosecutor: Finding critical flaws...
  ⚖️  Step 4/4  Judge: Assigning verdict and score...
  ✅ Analysis complete.
```

### 2. Rich Terminal Report
Once complete, a formatted, readable summary is printed directly to your console:
```text
  ╔══════════════════════════════════════════════════════════════════════╗
  ║          ThesisDefender — Adversarial Argument Analysis              ║
  ╚══════════════════════════════════════════════════════════════════════╝

  Job ID    cli_a1b2c3d4
  Timestamp 2026-06-21 14:00 UTC

  ORIGINAL ARGUMENT
  ────────────────────────────────────────────────────────────────────────
  AI will replace all programmers by 2030...

  🔍  ORCHESTRATOR — Claim & Assumptions
  ────────────────────────────────────────────────────────────────────────
  Main Claim
  All programming jobs will be replaced by AI by the year 2030.

  Implicit Assumptions
  • AI capabilities will continue to scale exponentially without plateauing.
  • Programming is primarily code generation rather than system design.
  ...

  ⚖️   JUDGE — Verdict
  ────────────────────────────────────────────────────────────────────────
  Resilience Score
  ███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  28 / 100
  WEAK

  The argument relies on heavily speculative timelines and ignores the...

  Critical Vulnerability
  ▶ Conflates "writing syntax" with "software engineering and architecture."

  Recommended Fixes
  → Narrow the timeline to specific junior coding tasks.
  → Acknowledge the shift toward AI-assisted engineering rather than full replacement.

  Stronger Version
  "AI will likely automate a vast majority of routine coding tasks by 2030, shifting the programmer's role from writing syntax to system architecture and prompt engineering."
```

### 3. JSON Artifact
The complete structured output is automatically saved to your current directory with the job ID:
```text
💾 Saved JSON report to: D:\ThesisDefender-Kaggle\report_cli_a1b2c3d4.json
```
