"""
ThesisDefender CLI — Main Entry Point
=======================================
Implements the `thesis-defender` command line interface.
Reuses the exact same ADK pipeline, security guards, and LLM clients
as the FastAPI backend, but runs entirely locally without a server.

Usage:
  thesis-defender analyze --input "AI will replace all programmers"
  thesis-defender analyze claim.md
"""

import sys
import os
import json
import uuid
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Ensure backend directory is in PYTHONPATH if run directly
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from config import settings
from services.model_client import create_model_client
from agents.pipeline import run_analysis
from security.guards import sanitize_argument, validate_argument, ArgumentRejected
from cli.queue import CliQueue
from cli.formatter import print_analysis


def _read_input(args: argparse.Namespace) -> str:
    """Read argument text from --input flag or positional file."""
    if args.input:
        return args.input

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File '{file_path}' not found.", file=sys.stderr)
            sys.exit(1)
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
            sys.exit(1)

    print("Error: Must provide either a file path or --input text.", file=sys.stderr)
    sys.exit(1)


async def _run_analyze(args: argparse.Namespace) -> None:
    """Execute the analyze command."""
    # 1. Read input
    raw_text = _read_input(args)

    # 2. Security Layer 1: Sanitize & Validate (exact same as FastAPI route)
    clean_text = sanitize_argument(raw_text)
    try:
        validate_argument(clean_text)
    except ArgumentRejected as e:
        print(f"\n❌ Input Rejected: {e}\n", file=sys.stderr)
        sys.exit(1)

    # 3. Setup dependencies
    job_id = f"cli_{uuid.uuid4().hex[:8]}"
    try:
        model_client = create_model_client()
    except Exception as e:
        print(f"\n❌ Model Client Error: {e}")
        print("Check your .env file and ensure MODEL_PROVIDER and API keys are set.\n", file=sys.stderr)
        sys.exit(1)

    cli_queue = CliQueue(show_progress=True)

    print(f"\n🚀 Starting ThesisDefender Analysis (Job: {job_id})")
    print(f"🤖 Provider: {model_client.provider.upper()}")
    print(f"🔄 Engine:   {'ADK Pipeline (mcp enabled)' if settings.USE_ADK else 'Standard Pipeline'}\n")

    # 4. Run pipeline
    # The pipeline is identical to the web route, we just pass the CLI queue adapter
    await run_analysis(
        job_id=job_id,
        argument=clean_text,
        model_client=model_client,
        foundry_client=None,
        queue=cli_queue,
    )

    # 5. Handle results
    if cli_queue.error or not cli_queue.result:
        print(f"\n❌ Analysis Failed: {cli_queue.error}\n", file=sys.stderr)
        sys.exit(1)

    # Print rich report
    print_analysis(cli_queue.result)

    # Save JSON report
    report_filename = f"report_{job_id}.json"
    report_path = Path(report_filename)
    report_path.write_text(
        cli_queue.result.model_dump_json(indent=2),
        encoding="utf-8"
    )
    print(f"💾 Saved JSON report to: {report_path.absolute()}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ThesisDefender CLI - Adversarial Argument Analysis"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'analyze' command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze an argument")
    analyze_parser.add_argument(
        "file", 
        nargs="?", 
        help="Path to a text or markdown file containing the argument"
    )
    analyze_parser.add_argument(
        "-i", "--input", 
        type=str, 
        help="Inline text of the argument to analyze"
    )

    args = parser.parse_args()

    if args.command == "analyze":
        # Check environment variables before starting
        from security.guards import audit_secrets
        issues = audit_secrets()
        for issue in issues:
            print(f"⚠️  Warning: {issue}", file=sys.stderr)
            
        try:
            asyncio.run(_run_analyze(args))
        except KeyboardInterrupt:
            print("\n\n🛑 Analysis cancelled by user.", file=sys.stderr)
            sys.exit(130)


if __name__ == "__main__":
    main()
