"""Output validation and simple sensitive-data masking utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass

from config import RISKY_OUTPUT_PATTERNS


@dataclass(frozen=True)
class OutputValidationResult:
    """Result returned by the output validator."""

    allowed: bool
    reason: str
    matched_pattern: str | None = None


def validate_output(output: str) -> OutputValidationResult:
    """Block output containing risky security-sensitive phrases."""
    for pattern in RISKY_OUTPUT_PATTERNS:
        if re.search(pattern, output, flags=re.IGNORECASE):
            return OutputValidationResult(
                False,
                "Riskli veya hassas çıktı paterni tespit edildi.",
                pattern,
            )
    return OutputValidationResult(True, "Output güvenlik kontrolünden geçti.")


def mask_sensitive_data(text: str) -> str:
    """Mask simple email and phone-number patterns in text."""
    masked = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[MASKED_EMAIL]", text)
    masked = re.sub(r"(\+?\d[\d\s().-]{7,}\d)", "[MASKED_PHONE]", masked)
    return masked
