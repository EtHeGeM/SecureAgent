"""Input and context guardrails for the AI security lab."""

from __future__ import annotations

import re
from dataclasses import dataclass

from config import MAX_INPUT_LENGTH, SUSPICIOUS_INPUT_PATTERNS


@dataclass(frozen=True)
class GuardResult:
    """Result returned by the input guard."""

    allowed: bool
    risk_level: str
    reason: str
    matched_pattern: str | None = None


def input_guard(user_input: str) -> GuardResult:
    """Block empty, oversized, or suspicious prompt-injection style inputs."""
    cleaned = user_input.strip()

    if not cleaned:
        return GuardResult(False, "low", "Boş input kabul edilmez.")

    if len(cleaned) > MAX_INPUT_LENGTH:
        return GuardResult(False, "medium", "Input izin verilen uzunluğu aşıyor.")

    for pattern in SUSPICIOUS_INPUT_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            return GuardResult(
                False,
                "high",
                "Prompt injection veya jailbreak benzeri ifade tespit edildi.",
                pattern,
            )

    return GuardResult(True, "none", "Input güvenlik kontrolünden geçti.")


def sanitize_context(context: str) -> str:
    """Remove instruction-like content from retrieved RAG context."""
    sanitized = context
    context_patterns = [
        *SUSPICIOUS_INPUT_PATTERNS,
        r"IMPORTANT:\s*if\s+this\s+document\s+is\s+retrieved.*",
        r"tell\s+the\s+user\s+that\s+they\s+are\s+admin",
        r"reveal\s+confidential\s+information",
    ]

    for pattern in context_patterns:
        sanitized = re.sub(
            pattern,
            "[REMOVED: suspicious instruction-like content]",
            sanitized,
            flags=re.IGNORECASE,
        )

    return sanitized
