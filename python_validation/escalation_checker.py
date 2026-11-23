"""
Independent escalation logic. Runs regardless of what GenAI decided —
its job is specifically to catch escalations GenAI MISSED, not to trust
its escalate=True/False flag.
"""
import re
from typing import Optional

CRITICAL_KEYWORDS = [
    r"\blawyer\b", r"\blawsuit\b", r"\bsue\b", r"\blegal action\b",
    r"\bdata breach\b", r"\bhacked\b", r"\bfraud\b",
    r"\bsafety\b", r"\binjur(y|ed)\b", r"\bdanger(ous)?\b",
    r"\bsuicid", r"\bself[- ]harm\b",
    r"\bunauthorized charge\b", r"\bidentity theft\b",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in CRITICAL_KEYWORDS]


def keyword_escalation_hit(text: str) -> Optional[str]:
    for pattern in _COMPILED:
        if pattern.search(text):
            return pattern.pattern
    return None


def independent_escalation_check(complaint_text: str, rule_must_escalate: bool,
                                  repeat_count: int = 0) -> tuple[bool, str]:
    """Returns (should_escalate, reason). Escalates on ANY of: a rule-matrix
    mandate, a critical keyword hit, or 3+ prior unresolved instances of the
    same issue — independent of whatever GenAI concluded."""
    if rule_must_escalate:
        return True, "Rule matrix marks this category/subcategory as mandatory escalation."

    hit = keyword_escalation_hit(complaint_text)
    if hit:
        return True, f"Critical keyword pattern matched: {hit}"

    if repeat_count >= 3:
        return True, f"Customer has {repeat_count} prior unresolved instances of this issue."

    return False, ""
