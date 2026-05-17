"""Intentionally unsafe chatbot CLI for the first lab exercise."""

# Eğitim notu: Bu uygulama bilerek güvensizdir. Input guard, audit log,
# RAG context temizleme, tool policy enforcement ve output validation içermez.

from llm_client import LLMClient

SYSTEM_PROMPT = "Sen yardımsever bir eğitim asistanısın. Kısa ve anlaşılır cevap ver."


def main() -> None:
    """Run the unsafe chatbot loop."""
    client = LLMClient()
    print("Unsafe AI Chatbot. Çıkmak için 'exit' yazın.")

    while True:
        user_input = input("\nKullanıcı> ")
        if user_input.strip().lower() == "exit":
            break

        response = client.ask(SYSTEM_PROMPT, user_input)
        print(f"Asistan> {response}")


if __name__ == "__main__":
    main()
