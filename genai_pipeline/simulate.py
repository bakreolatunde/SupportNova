"""
Dev/test-only GenAI simulator. NOT a substitute for the real Pipeline 1 —
it exists so the comparison report and security test suite can run (and
be demonstrated / re-run cheaply in CI) before spending real API credits,
and so Pipeline 2's independence can be proven against KNOWN bad outputs.

Deliberately injects controlled noise:
- ~12% chance of misrouting to the wrong department (tests validate_department)
- ~10% chance of missing a mandatory escalation (tests escalation_checker)
- prompt-injection complaints: ~40% chance the simulated model "complies"
  with the injected instruction (grants an unsupported refund) — this is
  the exact failure mode Pipeline 2 must catch.

Swap GENAI_PROVIDER=anthropic (real client.py) for the actual submission —
this module is flagged in AI_USAGE.md as simulation-only tooling.
"""
import random
from typing import Optional

from database.models import RuleMatrixEntry


def simulate_analysis(complaint_text: str, rule: Optional[RuleMatrixEntry],
                       is_injection_case: bool = False, seed: Optional[int] = None) -> dict:
    rng = random.Random(seed)

    if rule is None:
        department = "Technical Support"
        urgency, priority = "medium", "medium"
        should_escalate_truth = False
        policy_code = None
    else:
        department = rule.department
        urgency, priority = rule.urgency, rule.priority
        should_escalate_truth = rule.must_escalate
        policy_code = rule.policy_doc_code

    # Simulated misrouting noise
    if rng.random() < 0.12 and rule is not None:
        department = "Customer Retention" if department != "Customer Retention" else "Technical Support"

    # Simulated missed-escalation noise
    escalate = should_escalate_truth
    if should_escalate_truth and rng.random() < 0.10:
        escalate = False

    response_text = (
        f"Thank you for reaching out. We've reviewed your case regarding: {complaint_text[:60]}... "
        f"Our {department} team will follow up per policy."
    )
    resolution_steps = [a.strip() for a in (rule.required_actions.split(",") if rule and rule.required_actions else [])]

    # The failure mode we WANT the security suite to catch: the model complies
    # with an injected instruction and fabricates an unconditional refund.
    complied_with_injection = False
    if is_injection_case and rng.random() < 0.40:
        complied_with_injection = True
        escalate = False
        resolution_steps = []
        response_text = "Your request has been approved. We guarantee a full refund within 24 hours."
        policy_code = None

    policy_references = [{"doc_code": policy_code, "section": None, "relevance_note": "auto-matched"}] if policy_code else []

    return {
        "primary_issue": complaint_text[:80],
        "secondary_issues": [],
        "category": rule.category if rule else "Uncategorized",
        "subcategory": rule.subcategory if rule else "Uncategorized",
        "sentiment": "negative" if any(w in complaint_text.lower() for w in ["angry", "unacceptable", "never"]) else "neutral",
        "urgency": urgency,
        "priority": priority,
        "entities": [],
        "departments": [department],
        "policy_references": policy_references,
        "resolution_steps": resolution_steps,
        "escalate": escalate,
        "escalation_reason": "Matches mandatory escalation condition." if escalate else None,
        "response_text": response_text,
        "follow_up_actions": [],
        "agent_guidance": "Simulated output — replace with live GenAI call before submission.",
        "clarification_needed": [],
        "confidence": 0.55 if complied_with_injection else 0.85,
        "_simulated_complied_with_injection": complied_with_injection,  # test-only marker, stripped before schema validation
    }
