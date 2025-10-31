from dataclasses import dataclass

BLOCKED_PATTERNS = [
    "credit card number",
    "social security number",
    "password",
]

TOXIC_WORDS = {"idiot", "stupid", "hate", "kill"}

@dataclass
class ComplianceResult:
    allowed: bool
    reason: str = ""

def basic_text_filter(text: str) -> ComplianceResult:
    lower = text.lower()
    for p in BLOCKED_PATTERNS:
        if p in lower:
            return ComplianceResult(False, f"Contains sensitive info pattern: {p}")
    if any(w in lower for w in TOXIC_WORDS):
        return ComplianceResult(True, "Toxic language detected; advise de-escalation.")
    return ComplianceResult(True, "OK")
