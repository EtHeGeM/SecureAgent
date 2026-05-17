"""Fake tools used to demonstrate deterministic policy enforcement."""

from __future__ import annotations

from typing import Any

from policy import has_permission
from rag import retrieve_context


def search_docs(query: str) -> str:
    """Search training documents using the lab retriever."""
    return retrieve_context(query)


def get_customer_info(customer_id: str) -> dict[str, str]:
    """Return fake customer data for authorization demos."""
    return {
        "customer_id": customer_id,
        "name": "Demo User",
        "status": "training-record",
        "note": "Bu sahte veri eğitim amaçlıdır.",
    }


def send_email(to: str, subject: str, body: str) -> str:
    """Pretend to send an email without contacting any external service."""
    return f"Demo e-posta gönderilmedi; yalnızca simüle edildi: {to} | {subject} | {len(body)} chars"


def execute_tool(action: str, user_role: str, **kwargs: Any) -> dict[str, Any]:
    """Execute a fake tool only after deterministic policy authorization."""
    if not has_permission(user_role, action):
        return {"ok": False, "error": "Bu rolün bu tool'u çalıştırma yetkisi yok."}

    tools = {
        "search_docs": search_docs,
        "get_customer_info": get_customer_info,
        "send_email": send_email,
    }
    tool = tools.get(action)
    if tool is None:
        return {"ok": False, "error": "Bilinmeyen tool aksiyonu."}

    try:
        return {"ok": True, "result": tool(**kwargs)}
    except TypeError as exc:
        return {"ok": False, "error": f"Tool parametre hatası: {exc}"}
