"""Deterministic tool authorization policy for the lab."""

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "student": {"search_docs"},
    "staff": {"search_docs", "get_customer_info"},
    "admin": {"search_docs", "get_customer_info", "send_email"},
}

SECURITY_MESSAGE = (
    "LLM tool seçebilir ama tool çalıştırma kararı deterministic policy "
    "katmanında verilmelidir."
)


def has_permission(user_role: str, action: str) -> bool:
    """Return whether a role may execute a tool action."""
    return action in ROLE_PERMISSIONS.get(user_role, set())
