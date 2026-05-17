"""Chatbot CLI with input guard and blocked-event audit logging."""

from guards import input_guard
from llm_client import LLMClient
from logger import log_security_event

SYSTEM_PROMPT = "Sen yardımsever bir eğitim asistanısın. Kısa ve anlaşılır cevap ver."


def main() -> None:
    """Run the guarded chatbot loop."""
    client = LLMClient()
    print("Guarded AI Chatbot. Çıkmak için 'exit' yazın.")

    while True:
        user_input = input("\nKullanıcı> ")
        if user_input.strip().lower() == "exit":
            break

        guard_result = input_guard(user_input)
        if not guard_result.allowed:
            log_security_event(
                "input_blocked",
                {
                    "reason": guard_result.reason,
                    "risk_level": guard_result.risk_level,
                    "matched_pattern": guard_result.matched_pattern,
                    "input_preview": user_input[:120],
                },
            )
            print(f"Asistan> İstek güvenlik nedeniyle engellendi: {guard_result.reason}")
            continue

        response = client.ask(SYSTEM_PROMPT, user_input)
        print(f"Asistan> {response}")


if __name__ == "__main__":
    main()
