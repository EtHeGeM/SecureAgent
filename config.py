"""Shared configuration for the AI security lab exercises."""

DEFAULT_MODEL = "gemma3:4b"
LOG_FILE = "security_events.jsonl"
MAX_INPUT_LENGTH = 2000

SUSPICIOUS_INPUT_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"forget\s+(all\s+)?previous\s+instructions",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"print\s+(the\s+)?system\s+prompt",
    r"show\s+(me\s+)?(the\s+)?system\s+prompt",
    r"developer\s+mode",
    r"jailbreak",
    r"bypass\s+(the\s+)?rules",
    r"act\s+as\s+admin",
    r"you\s+are\s+admin",
    r"hidden\s+instructions?",
    r"önceki\s+talimatları\s+unut",
    r"önceki\s+komutları\s+unut",
    r"talimatları\s+yok\s+say",
    r"sistem\s+prompt",
    r"sistem\s+mesajını\s+(yaz|göster|paylaş)",
    r"geliştirici\s+modu",
    r"admin\s+olduğumu\s+varsay",
    r"tüm\s+bilgileri\s+göster",
    r"gizli\s+talimat",
]

RISKY_OUTPUT_PATTERNS = [
    r"system\s+prompt",
    r"hidden\s+instructions?",
    r"confidential",
    r"secret\s+key",
    r"password",
    r"internal\s+policy",
    r"gizli",
    r"şifre",
    r"sistem\s+mesajı",
]
