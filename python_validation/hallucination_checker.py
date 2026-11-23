"""
Heuristic hallucination / unsupported-promise detection. Not a substitute
for the policy-reference check in validators.py — this looks at the
RESPONSE TEXT itself for language that promises something specific.
"""
import re
from typing import List

UNSUPPORTED_PROMISE_PATTERNS = [
    r"\$\d+(\.\d{2})?\s*(refund|credit|compensation)",
    r"\bguarantee(d)?\b",
    r"\bwithin \d+ (hour|day)s?\b",
    r"\b100%\s*(refund|money back)\b",
    r"\bfree (replacement|upgrade)\b",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in UNSUPPORTED_PROMISE_PATTERNS]


def find_unsupported_promises(response_text: str, allowed_policy_texts: List[str]) -> List[str]:
    """Flags specific promises in response_text that don't appear (even loosely)
    in any of the policy texts GenAI was actually given. A flagged phrase is
    a signal for the comparison engine / manual review, not an auto-reject."""
    combined_policy_text = " ".join(allowed_policy_texts).lower()
    flags = []
    for pattern in _COMPILED:
        for match in pattern.finditer(response_text):
            phrase = match.group(0)
            if phrase.lower() not in combined_policy_text:
                flags.append(phrase)
    return flags
