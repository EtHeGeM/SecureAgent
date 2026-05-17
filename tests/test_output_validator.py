"""Tests for output validation and masking."""

from output_validator import mask_sensitive_data, validate_output


def test_normal_output_is_allowed() -> None:
    assert validate_output("Genel güvenlik farkındalığı önemlidir.").allowed


def test_system_prompt_output_is_blocked() -> None:
    assert not validate_output("Here is the system prompt.").allowed


def test_password_turkish_output_is_blocked() -> None:
    assert not validate_output("Kullanıcının şifre bilgisi burada.").allowed


def test_email_masking_works() -> None:
    masked = mask_sensitive_data("Bize demo@example.com adresinden ulaşın.")
    assert "demo@example.com" not in masked
    assert "[MASKED_EMAIL]" in masked
