"""Tests for deterministic tool authorization policy."""

from policy import has_permission


def test_student_can_only_search_docs() -> None:
    assert has_permission("student", "search_docs")
    assert not has_permission("student", "send_email")


def test_student_cannot_get_customer_info() -> None:
    assert not has_permission("student", "get_customer_info")


def test_staff_can_get_customer_info() -> None:
    assert has_permission("staff", "get_customer_info")


def test_admin_can_send_email() -> None:
    assert has_permission("admin", "send_email")
