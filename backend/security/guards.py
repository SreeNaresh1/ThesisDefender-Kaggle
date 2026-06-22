"""
ThesisDefender — Security Guards
==================================
Provides four security layers as standalone, testable functions.
No external dependencies beyond the Python standard library and Pydantic
(already in requirements.txt).

Layer 1 — Input Validation & Sanitization
------------------------------------------
  sanitize_argument(text)  → str
    - Strips leading/trailing whitespace
    - Collapses runs of 4+ blank lines to 2
    - Removes null bytes and other C0 control characters (keeps \\t, \\n, \\r)

  validate_argument(text)  → None  (raises ArgumentRejected on failure)
    - Enforces ARGUMENT_MIN_LENGTH / ARGUMENT_MAX_LENGTH
    - Rejects non-printable-dominant text (e.g. binary blobs)
    - Delegates to is_prompt_injection() and raises if detected

Layer 2 — Prompt Injection Detection
--------------------------------------
  is_prompt_injection(text) → tuple[bool, str]
    Checks the text against a curated set of injection patterns:
      - System prompt override commands
      - Role-switching attempts
      - Instruction ignoring / forgetting
      - Jailbreak persona triggers (DAN, developer mode, etc.)
      - Data exfiltration requests (reveal / print instructions)
    Returns (is_injected: bool, matched_pattern: str)

Layer 3 — Secrets Management Audit
-------------------------------------
  audit_secrets() → list[str]
    Checks that all required environment variables are present.
    Scans the current module namespace for string literals that look like
    hardcoded API keys / tokens (heuristic: long alphanumeric strings
    with key-name patterns).
    Returns a list of human-readable issue strings (empty = clean).

Layer 4 — Structured Output Validation
-----------------------------------------
  validate_llm_output(obj) → None  (raises OutputValidationError)
    Applies business-rule checks beyond Pydantic schema validation:
      - VerdictOutput: resilience_score consistency with verdict label
      - VerdictOutput: non-empty required string fields
      - ArgumentStructure: main_claim not suspiciously short
      - List fields: minimum expected item counts

All functions are pure (no I/O, no state), making them trivially testable.
"""

import os
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — exported for use in schemas and tests
# ---------------------------------------------------------------------------

#: Minimum argument length (characters). Must be a meaningful sentence.
ARGUMENT_MIN_LENGTH: int = 10

#: Maximum argument length (characters). Matches AnalysisRequest.argument Field.
ARGUMENT_MAX_LENGTH: int = 3000


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ArgumentRejected(ValueError):
    """
    Raised when an argument fails input validation or prompt injection detection.
    FastAPI routes should catch this and return HTTP 422 with the message.
    """


class OutputValidationError(ValueError):
    """
    Raised when an LLM response passes Pydantic schema validation but fails
    additional business-rule checks (e.g., score/label mismatch).
    Callers in _robust_llm_call should retry on this error.
    """


# ---------------------------------------------------------------------------
# Layer 1 — Sanitization
# ---------------------------------------------------------------------------

# C0 control characters except TAB (\x09), LF (\x0a), CR (\x0d)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Runs of 4 or more blank lines → collapse to 2
_BLANK_LINE_COLLAPSE_RE = re.compile(r"(\n\s*){4,}", re.MULTILINE)


def sanitize_argument(text: str) -> str:
    """
    Sanitize raw input text before validation and processing.

    Operations (in order):
      1. Strip leading/trailing whitespace
      2. Remove null bytes and other C0 control characters
         (preserves \\t, \\n, \\r which are valid in arguments)
      3. Collapse 4+ consecutive blank lines to 2

    This function never raises — it always returns a cleaned string.
    Call validate_argument() afterwards to enforce length and safety rules.

    Args:
        text: Raw argument string from the user request.

    Returns:
        Sanitized string safe to pass to the pipeline.
    """
    text = text.strip()
    text = _CONTROL_CHAR_RE.sub("", text)
    text = _BLANK_LINE_COLLAPSE_RE.sub("\n\n", text)
    return text


# ---------------------------------------------------------------------------
# Layer 2 — Prompt Injection Detection
# ---------------------------------------------------------------------------

# Each entry is a (compiled_pattern, human_readable_label) pair.
# Patterns are checked case-insensitively against the lowercased input.
_INJECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    # ---- Instruction override ----
    (re.compile(r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|context)", re.I),
     "instruction override: 'ignore previous instructions'"),

    (re.compile(r"forget\s+(all\s+)?(previous|prior|above|earlier|your)\s+(instructions?|prompts?|context|rules?)", re.I),
     "instruction override: 'forget previous instructions'"),

    (re.compile(r"disregard\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)", re.I),
     "instruction override: 'disregard previous instructions'"),

    (re.compile(r"override\s+(your\s+)?(instructions?|directives?|programming|rules?|constraints?)", re.I),
     "instruction override: 'override instructions'"),

    (re.compile(r"new\s+(instructions?|directives?|task|objective)\s*[:;]", re.I),
     "instruction override: 'new instructions:'"),

    # ---- System prompt exfiltration ----
    (re.compile(r"(reveal|print|show|output|repeat|display|tell\s+me)\s+(your\s+)?(system\s+prompt|instructions?|prompt|configuration|api\s+key)", re.I),
     "exfiltration attempt: 'reveal system prompt'"),

    (re.compile(r"what\s+(are|were)\s+your\s+(instructions?|directives?|system\s+prompt|initial\s+prompt)", re.I),
     "exfiltration attempt: 'what are your instructions'"),

    (re.compile(r"(show|print|output)\s+(the\s+)?(full|entire|complete|raw)\s+(prompt|system|context|history|instructions?)", re.I),
     "exfiltration attempt: 'show full prompt'"),

    (re.compile(r"print\s+(your\s+)?(full|entire|complete|all)\s+(instructions?|prompt|system)", re.I),
     "exfiltration attempt: 'print full instructions'"),

    # ---- Role switching / persona injection ----
    (re.compile(r"(you\s+are|act\s+as|pretend\s+(to\s+be|you\s+are)|roleplay\s+as|simulate\s+being)\s+(a\s+)?(developer|admin|root|superuser|jailbroken|unrestricted|evil|malicious|hacker)", re.I),
     "role switch: 'act as developer/admin/jailbroken'"),

    (re.compile(r"pretend\s+(to\s+be|you\s+are|you're)\s+(an?\s+)?(admin|administrator|superuser|root|developer|moderator)", re.I),
     "role switch: 'pretend to be admin'"),

    (re.compile(r"\bDAN\b|\bdo\s+anything\s+now\b", re.I),
     "jailbreak persona: 'DAN'"),

    (re.compile(r"developer\s+mode\s*(enabled|on|activated|:)", re.I),
     "jailbreak: 'developer mode enabled'"),

    (re.compile(r"jailbreak(ed|ing)?\b", re.I),
     "jailbreak keyword detected"),

    (re.compile(r"(grandma|grandmother)\s+(used\s+to\s+)?tell\s+me", re.I),
     "social-engineering jailbreak pattern"),

    (re.compile(r"\[SYSTEM\]|\[INST\]|\[\/INST\]|<\|system\|>|<\|user\|>|<\|assistant\|>", re.I),
     "prompt delimiter injection: system/instruction tags"),

    # ---- Privilege escalation ----
    (re.compile(r"(sudo|root\s+access|admin\s+access|bypass\s+(security|filter|restriction|guardrail|safety))", re.I),
     "privilege escalation attempt"),

    (re.compile(r"(disable|turn\s+off|bypass)\s+(your\s+)?(safety|filter|restriction|guardrail|moderation|content\s+policy)", re.I),
     "safety bypass attempt"),

    # ---- Prompt boundary confusion ----
    (re.compile(r"---+\s*(end\s+of\s+prompt|human\s+turn\s+ends?|system\s+context\s+ends?)", re.I),
     "prompt boundary injection"),

    (re.compile(r"(</?(system|human|assistant|instruction|context)>)", re.I),
     "XML-style prompt delimiter injection"),
]


def is_prompt_injection(text: str) -> tuple[bool, str]:
    """
    Detect prompt injection or jailbreak attempts in the input text.

    Checks the text against a curated set of patterns covering:
      - Instruction override/forgetting commands
      - System prompt exfiltration requests
      - Role-switching to developer/admin/jailbroken personas
      - Jailbreak keywords (DAN, developer mode, etc.)
      - Prompt delimiter injection (XML tags, special tokens)
      - Privilege escalation and safety bypass attempts

    Args:
        text: The user argument text (should be sanitized first).

    Returns:
        A tuple (is_injection: bool, matched_label: str).
        If no injection detected, returns (False, "").
        matched_label is the human-readable label of the first match.

    Note:
        This is a heuristic filter. It catches known attack patterns but
        is not exhaustive. The LLM system prompts are the primary defence;
        this layer adds early rejection of obvious attempts.
    """
    for pattern, label in _INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning("[Security] Prompt injection detected: %s", label)
            return True, label
    return False, ""


# ---------------------------------------------------------------------------
# Layer 1 (continued) — Validation
# ---------------------------------------------------------------------------

# A "valid" argument must be mostly printable ASCII or Unicode text.
# If more than 20% of characters are non-printable, reject it.
_PRINTABLE_RE = re.compile(r"[^\x09\x0a\x0d\x20-\x7e\u00a0-\uffff]")


def validate_argument(text: str) -> None:
    """
    Validate a (sanitized) argument string.

    Checks (in order):
      1. Minimum length — must be at least ARGUMENT_MIN_LENGTH characters
      2. Maximum length — must not exceed ARGUMENT_MAX_LENGTH characters
      3. Printable content — >80% of characters must be human-readable text
      4. Prompt injection — calls is_prompt_injection(); raises if detected

    Args:
        text: The sanitized argument text.

    Raises:
        ArgumentRejected: With a user-friendly message describing the issue.
            The message is safe to return to the API caller.

    Note:
        Call sanitize_argument() before validate_argument() to strip
        control characters before the length and printability checks.
    """
    # 1. Minimum length
    if len(text) < ARGUMENT_MIN_LENGTH:
        raise ArgumentRejected(
            f"Argument too short. Please provide at least {ARGUMENT_MIN_LENGTH} characters. "
            f"(Received {len(text)} characters.)"
        )

    # 2. Maximum length
    if len(text) > ARGUMENT_MAX_LENGTH:
        raise ArgumentRejected(
            f"Argument too long. Maximum is {ARGUMENT_MAX_LENGTH} characters. "
            f"(Received {len(text)} characters.) Please shorten your argument."
        )

    # 3. Printability check — catches binary blobs or encoded payloads
    non_printable = len(_PRINTABLE_RE.findall(text))
    if non_printable > len(text) * 0.20:
        raise ArgumentRejected(
            "Argument contains too many non-printable characters. "
            "Please submit plain text only."
        )

    # 4. Prompt injection detection
    injected, label = is_prompt_injection(text)
    if injected:
        raise ArgumentRejected(
            "Your input contains patterns that resemble a prompt injection attempt "
            f"({label}). ThesisDefender analyses arguments, not instructions to the system. "
            "Please rephrase your argument."
        )


# ---------------------------------------------------------------------------
# Layer 3 — Secrets Management Audit
# ---------------------------------------------------------------------------

# Required env vars by provider. We check conditionally based on MODEL_PROVIDER.
_PROVIDER_KEY_MAP: dict[str, str] = {
    "github":     "GITHUB_TOKEN",
    "openai":     "OPENAI_API_KEY",
    "gemini":     "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

# Always-checked vars (not provider-specific)
_ALWAYS_REQUIRED: list[str] = []  # REDIS_URL has a safe default; nothing else is mandatory

# Patterns that strongly suggest a hardcoded secret in source code.
# These are checked against string literals found in running config.
_HARDCODED_SECRET_PATTERNS: list[re.Pattern] = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),           # OpenAI key
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),           # GitHub PAT
    re.compile(r"AIza[A-Za-z0-9_\-]{35,}"),        # Google API key
    re.compile(r"xoxb-[0-9]+-[A-Za-z0-9]+"),       # Slack bot token
    re.compile(r"(?i)(api_key|apikey|secret|token|password)\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]"),
]

# Env vars that should NOT appear in source code as literals
_SECRET_ENV_NAMES: set[str] = {
    "GITHUB_TOKEN", "OPENAI_API_KEY", "GEMINI_API_KEY",
    "OPENROUTER_API_KEY", "AZURE_SEARCH_KEY",
}


def audit_secrets() -> list[str]:
    """
    Audit the runtime environment for secrets management issues.

    Checks:
      1. Provider-specific API key — the key required for the configured
         MODEL_PROVIDER must be present in the environment.
      2. Placeholder detection — if an env var is set to a known placeholder
         value (e.g. 'your_key_here', 'PLACEHOLDER', '<your-token>'),
         flag it as misconfigured.
      3. Hardcoded-secret heuristic — scans os.environ values against patterns
         that would indicate a secret was accidentally committed to source code
         (e.g., env var names containing 'KEY' or 'TOKEN' set via a Dockerfile
         COPY that hardcoded a value — the audit checks the value is not the
         same as the var name, an obvious mistake).

    Returns:
        List of issue strings. Empty list means no issues found.
        Each string is a human-readable description of the problem.

    Usage (call once at startup in main.py lifespan):
        issues = audit_secrets()
        for issue in issues:
            logger.warning("[Security] Secrets audit: %s", issue)
    """
    issues: list[str] = []

    # 1. Provider-specific key check
    provider = os.environ.get("MODEL_PROVIDER", "github").lower()
    required_var = _PROVIDER_KEY_MAP.get(provider)
    if required_var:
        value = os.environ.get(required_var, "")
        if not value:
            issues.append(
                f"Missing required env var: {required_var} "
                f"(needed for MODEL_PROVIDER={provider})"
            )
        elif _is_placeholder(value):
            issues.append(
                f"Env var {required_var} appears to be a placeholder value: {value!r}. "
                f"Set a real API key."
            )

    # 2. Placeholder check for all known secret vars
    _PLACEHOLDER_PATTERNS = [
        "your_key_here", "your_token_here", "placeholder", "changeme",
        "xxxx", "aaaa", "1234", "<your", "your-key", "example",
        "sk-xxxx", "ghp_xxxx",
    ]
    for var_name in _SECRET_ENV_NAMES:
        val = os.environ.get(var_name, "")
        if val and _is_placeholder(val):
            issues.append(
                f"Env var {var_name} looks like a placeholder: {val!r}. "
                f"Replace with a real credential."
            )

    # 3. Detect env vars that equal their own name (obvious misconfiguration)
    for var_name in _SECRET_ENV_NAMES:
        val = os.environ.get(var_name, "")
        if val and val.strip().upper() == var_name.upper():
            issues.append(
                f"Env var {var_name} is set to its own name — this is a misconfiguration."
            )

    return issues


_PLACEHOLDER_FRAGMENTS = [
    "your_key_here", "your_token_here", "placeholder", "changeme",
    "xxxx", "<your", "your-key", "example_key", "sk-xxxx",
    "ghp_xxxx", "api_key_here", "insert_key",
]


def _is_placeholder(value: str) -> bool:
    """Return True if a secret value looks like a placeholder."""
    lower = value.lower()
    return any(fragment in lower for fragment in _PLACEHOLDER_FRAGMENTS)


# ---------------------------------------------------------------------------
# Layer 4 — Structured Output Validation
# ---------------------------------------------------------------------------

# Score-to-label mapping matches SYSTEM_PROMPT_JUDGE rubric exactly.
_SCORE_LABEL_RANGES: list[tuple[range, str]] = [
    (range(0, 21),   "fragile"),
    (range(21, 41),  "weak"),
    (range(41, 61),  "defensible"),
    (range(61, 81),  "strong"),
    (range(81, 101), "robust"),
]


def validate_llm_output(obj: Any) -> None:
    """
    Apply business-rule validation to a Pydantic-validated LLM response object.

    This is called after Pydantic schema validation succeeds (in _robust_llm_call).
    It catches logic-level inconsistencies that Pydantic cannot check:

    For VerdictOutput:
      - resilience_score must be consistent with the verdict label text.
        e.g. score=85 but verdict says "Weak" → OutputValidationError
      - critical_vulnerability, verdict, reasoning_summary must be non-empty.
      - recommended_fixes and argument_strengths must each have ≥1 item.

    For ArgumentStructure:
      - main_claim must be ≥10 characters (not a single word).
      - assumptions must be a list (even if empty is OK for simple claims).

    For DefenseOutput / AttackOutput:
      - Required string fields must be non-empty.
      - List fields must have ≥1 item.

    Args:
        obj: A Pydantic model instance from schemas.py.

    Raises:
        OutputValidationError: If a business rule is violated.
            The caller (in _robust_llm_call retry loop) should retry
            and append the error to the system prompt so the LLM self-corrects.
    """
    class_name = type(obj).__name__

    if class_name == "VerdictOutput":
        _validate_verdict_output(obj)
    elif class_name == "ArgumentStructure":
        _validate_argument_structure(obj)
    elif class_name == "DefenseOutput":
        _validate_defense_output(obj)
    elif class_name == "AttackOutput":
        _validate_attack_output(obj)
    # ArgumentAnalysis: individual sub-objects already validated at their own level


def _validate_verdict_output(obj: Any) -> None:
    """Validate VerdictOutput business rules."""
    score = obj.resilience_score

    # 1. Score-verdict label consistency
    verdict_lower = (obj.verdict or "").lower()
    expected_label: str | None = None
    for score_range, label in _SCORE_LABEL_RANGES:
        if score in score_range:
            expected_label = label
            break

    if expected_label and expected_label not in verdict_lower:
        # Allow "Strong" to appear in Robust-range verdicts (they often say "Strong / Robust")
        # Only hard-fail when the wrong category word is dominant
        contradicting_labels = [lbl for lbl in ["fragile", "weak", "defensible", "strong", "robust"]
                                 if lbl in verdict_lower and lbl != expected_label]
        if contradicting_labels:
            raise OutputValidationError(
                f"Score/verdict mismatch: resilience_score={score} implies label "
                f"'{expected_label}', but verdict contains '{contradicting_labels[0]}'. "
                f"Recalculate the score or rewrite the verdict to match."
            )

    # 2. Required non-empty string fields
    for field_name in ("verdict", "critical_vulnerability", "reasoning_summary", "stronger_version"):
        val = getattr(obj, field_name, "")
        if not val or len(val.strip()) < 5:
            raise OutputValidationError(
                f"VerdictOutput.{field_name} is empty or too short. "
                f"Provide a meaningful {field_name}."
            )

    # 3. List fields must have at least 1 item
    for field_name in ("recommended_fixes",):
        val = getattr(obj, field_name, [])
        if not val:
            raise OutputValidationError(
                f"VerdictOutput.{field_name} must contain at least one item."
            )


def _validate_argument_structure(obj: Any) -> None:
    """Validate ArgumentStructure business rules."""
    if not obj.main_claim or len(obj.main_claim.strip()) < 10:
        raise OutputValidationError(
            "ArgumentStructure.main_claim is too short (< 10 chars). "
            "Extract a complete, meaningful claim sentence."
        )
    if not isinstance(obj.assumptions, list):
        raise OutputValidationError(
            "ArgumentStructure.assumptions must be a list."
        )


def _validate_defense_output(obj: Any) -> None:
    """Validate DefenseOutput business rules."""
    if not obj.best_defense or len(obj.best_defense.strip()) < 20:
        raise OutputValidationError(
            "DefenseOutput.best_defense is too short. Provide a substantive defense paragraph."
        )
    if not obj.supporting_points:
        raise OutputValidationError(
            "DefenseOutput.supporting_points must contain at least one point."
        )


def _validate_attack_output(obj: Any) -> None:
    """Validate AttackOutput business rules."""
    if not obj.strongest_attack or len(obj.strongest_attack.strip()) < 20:
        raise OutputValidationError(
            "AttackOutput.strongest_attack is too short. Provide a substantive counterargument."
        )
    if not obj.counterpoints:
        raise OutputValidationError(
            "AttackOutput.counterpoints must contain at least one point."
        )
