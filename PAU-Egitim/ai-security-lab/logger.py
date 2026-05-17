"""JSONL audit logging helpers for security-relevant events."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import LOG_FILE


def log_security_event(event_type: str, data: dict[str, Any]) -> None:
    """Append a security event to the JSONL audit log."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "data": data,
    }

    try:
        with Path(LOG_FILE).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"Audit log yazılamadı: {exc}")
