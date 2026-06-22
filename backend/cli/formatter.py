"""
ThesisDefender CLI — Output Formatter
=======================================
Renders an ArgumentAnalysis result as a rich, readable terminal report
using only Python's standard library (no Rich, no Colorama required).

The formatter uses ANSI escape codes for colour and bold text. When stdout
is not a TTY (e.g. piped to a file), ANSI codes are automatically suppressed.

Public API:
    print_analysis(analysis: ArgumentAnalysis) -> None
        Print the full report to stdout.

    format_analysis(analysis: ArgumentAnalysis) -> str
        Return the full report as a plain string (ANSI stripped).
"""

import sys
import json
from typing import Optional

from config import settings

from models.schemas import ArgumentAnalysis, get_score_label


# ---------------------------------------------------------------------------
# ANSI helpers — auto-disabled when stdout is not a TTY
# ---------------------------------------------------------------------------

_USE_COLOUR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    """Wrap text in an ANSI escape if stdout is a TTY."""
    if not _USE_COLOUR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _bold(t: str)       -> str: return _c("1", t)
def _dim(t: str)        -> str: return _c("2", t)
def _green(t: str)      -> str: return _c("32", t)
def _red(t: str)        -> str: return _c("31", t)
def _yellow(t: str)     -> str: return _c("33", t)
def _cyan(t: str)       -> str: return _c("36", t)
def _magenta(t: str)    -> str: return _c("35", t)
def _blue(t: str)       -> str: return _c("34", t)
def _bold_green(t: str) -> str: return _c("1;32", t)
def _bold_red(t: str)   -> str: return _c("1;31", t)
def _bold_yellow(t: str)-> str: return _c("1;33", t)
def _bold_cyan(t: str)  -> str: return _c("1;36", t)


def _hr(char: str = "─", width: int = 72) -> str:
    return _dim(char * width)


# ---------------------------------------------------------------------------
# Score colouring
# ---------------------------------------------------------------------------

def _score_colour(score: int, text: str) -> str:
    if score <= 20:   return _bold_red(text)
    if score <= 40:   return _red(text)
    if score <= 60:   return _yellow(text)
    if score <= 80:   return _bold_green(text)
    return _bold_cyan(text)


def _score_bar(score: int, width: int = 40) -> str:
    """Return a filled/empty bar representing the resilience score."""
    filled = round(score / 100 * width)
    empty  = width - filled
    bar = "█" * filled + "░" * empty
    return _score_colour(score, bar)


# ---------------------------------------------------------------------------
# Bullet list helper
# ---------------------------------------------------------------------------

def _bullets(items: list[str], indent: str = "  ", bullet: str = "•") -> str:
    return "\n".join(f"{indent}{_dim(bullet)} {item}" for item in items)


# ---------------------------------------------------------------------------
# Main formatter
# ---------------------------------------------------------------------------

def format_analysis(analysis: ArgumentAnalysis) -> str:
    """
    Render an ArgumentAnalysis as a multi-section terminal report string.

    Sections:
      Header         — title + timestamp + job id
      Argument       — original argument text
      Claim          — extracted main claim + assumptions
      Defence        — steel-man + supporting points
      Attack         — strongest counterargument + counterpoints
      Verdict        — score bar, label, vulnerability, fixes, stronger version
      Summary        — reasoning summary
      Footer         — processing time + LLM call count

    Returns:
        A string with ANSI codes when stdout is a TTY, plain text otherwise.
    """
    v = analysis.verdict
    score = v.resilience_score
    label = get_score_label(score)
    ts = analysis.analysis_timestamp.strftime("%Y-%m-%d %H:%M UTC")
    processing_s = analysis.processing_time_ms / 1000

    lines: list[str] = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines += [
        "",
        _bold_cyan("  ╔══════════════════════════════════════════════════════════════════════╗"),
        _bold_cyan("  ║          ThesisDefender — Adversarial Argument Analysis              ║"),
        _bold_cyan("  ╚══════════════════════════════════════════════════════════════════════╝"),
        "",
        f"  {_dim('Job ID')}    {_dim(analysis.job_id)}",
        f"  {_dim('Timestamp')} {_dim(ts)}",
        "",
    ]

    # ── Argument ─────────────────────────────────────────────────────────────
    lines += [
        _hr(),
        _bold("  ORIGINAL ARGUMENT"),
        _hr(),
        "",
    ]
    for para in analysis.original_argument.split("\n"):
        lines.append(f"  {para}" if para.strip() else "")
    lines.append("")

    # ── Claim Structure ──────────────────────────────────────────────────────
    lines += [
        _hr(),
        _bold("  🔍  ORCHESTRATOR — Claim & Assumptions"),
        _hr(),
        "",
        f"  {_bold('Main Claim')}",
        f"  {_cyan(analysis.structure.main_claim)}",
        "",
    ]
    if analysis.structure.assumptions:
        lines += [
            f"  {_bold('Implicit Assumptions')}",
            _bullets(analysis.structure.assumptions),
            "",
        ]

    # ── Defence ──────────────────────────────────────────────────────────────
    lines += [
        _hr(),
        _bold("  🛡️   DEFENSE COUNSEL — Steel-Man"),
        _hr(),
        "",
        f"  {analysis.defense.best_defense}",
        "",
    ]
    if analysis.defense.supporting_points:
        lines += [
            f"  {_bold('Supporting Points')}",
            _bullets(analysis.defense.supporting_points),
            "",
        ]

    # ── Attack ───────────────────────────────────────────────────────────────
    lines += [
        _hr(),
        _bold("  ⚔️   PROSECUTOR — Strongest Attack"),
        _hr(),
        "",
        f"  {analysis.attack.strongest_attack}",
        "",
    ]
    if analysis.attack.counterpoints:
        lines += [
            f"  {_bold('Counterpoints')}",
            _bullets(analysis.attack.counterpoints),
            "",
        ]

    # ── Verdict ──────────────────────────────────────────────────────────────
    lines += [
        _hr(),
        _bold("  ⚖️   JUDGE — Verdict"),
        _hr(),
        "",
        f"  {_bold('Resilience Score')}",
        f"  {_score_bar(score)}  {_score_colour(score, _bold(str(score)))} / 100",
        f"  {_score_colour(score, _bold(label.upper()))}",
        "",
        f"  {v.verdict}",
        "",
        f"  {_bold('Critical Vulnerability')}",
        f"  {_red('▶')} {v.critical_vulnerability}",
        "",
    ]
    if v.recommended_fixes:
        lines += [
            f"  {_bold('Recommended Fixes')}",
            _bullets(v.recommended_fixes, bullet="→"),
            "",
        ]
    lines += [
        f"  {_bold('Stronger Version')}",
        f"  {_green('\"')}{_green(v.stronger_version)}{_green('\"')}",
        "",
    ]

    # ── Reasoning Summary ────────────────────────────────────────────────────
    lines += [
        _hr(),
        _bold("  📋  REASONING SUMMARY"),
        _hr(),
        "",
        f"  {v.reasoning_summary}",
        "",
    ]

    # ── Footer ───────────────────────────────────────────────────────────────
    lines += [
        _hr("─"),
        _dim(f"  ⏱  Processed in {processing_s:.1f}s  ·  {analysis.total_llm_calls} LLM calls"),
        _dim(f"  🤖 Pipeline: {'ADK SequentialAgent' if settings.USE_ADK else 'Standard Pipeline'}"),
        "",
    ]

    return "\n".join(lines)


def print_analysis(analysis: ArgumentAnalysis) -> None:
    """Print a formatted analysis report to stdout."""
    print(format_analysis(analysis))
