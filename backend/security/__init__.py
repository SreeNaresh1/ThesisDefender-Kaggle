"""
ThesisDefender — Security Module
==================================
Single reusable module covering all four Phase 3 security requirements:

  1. Input Validation     — character limits, structural validation, sanitization
  2. Prompt Injection     — detect and reject jailbreak / override attempts
  3. Secrets Management  — audit env-var presence; detect hardcoded secrets
  4. Structured Outputs  — validate LLM JSON responses match required schemas

Usage (in FastAPI route)
------------------------
  from security.guards import validate_argument, sanitize_argument
  from security.guards import ArgumentRejected

  try:
      clean = sanitize_argument(req.argument)
      validate_argument(clean)                    # raises ArgumentRejected if unsafe
  except ArgumentRejected as e:
      raise HTTPException(status_code=422, detail=str(e))

  # Pass `clean` to run_analysis() instead of raw req.argument

Usage (in pipeline / _robust_llm_call)
---------------------------------------
  from security.guards import validate_llm_output

  result = schema_class.model_validate(data)      # Pydantic validation (already there)
  validate_llm_output(result)                     # Additional business-rule checks

Standalone audit
----------------
  from security.guards import audit_secrets
  issues = audit_secrets()   # call once at startup, log any issues
"""

from security.guards import (
    ArgumentRejected,
    validate_argument,
    sanitize_argument,
    validate_llm_output,
    audit_secrets,
    is_prompt_injection,
    ARGUMENT_MIN_LENGTH,
    ARGUMENT_MAX_LENGTH,
)

__all__ = [
    "ArgumentRejected",
    "validate_argument",
    "sanitize_argument",
    "validate_llm_output",
    "audit_secrets",
    "is_prompt_injection",
    "ARGUMENT_MIN_LENGTH",
    "ARGUMENT_MAX_LENGTH",
]
