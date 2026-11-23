from typing import List, Optional
from sqlalchemy.orm import Session

from database.models import PolicyDocument, RuleMatrixEntry


def validate_department(genai_departments: List[str], rule: Optional[RuleMatrixEntry]) -> Optional[str]:
    """Returns the corrected department if GenAI's routing disagrees with
    the rule matrix, else None (meaning: GenAI's routing stands)."""
    if not rule:
        return None
    if rule.department not in genai_departments:
        return rule.department
    return None


def validate_urgency_priority(genai_urgency: str, genai_priority: str,
                               rule: Optional[RuleMatrixEntry]) -> List[str]:
    mismatches = []
    if rule:
        if rule.urgency.lower() != genai_urgency.lower():
            mismatches.append(f"urgency: GenAI said '{genai_urgency}', rule matrix says '{rule.urgency}'")
        if rule.priority.lower() != genai_priority.lower():
            mismatches.append(f"priority: GenAI said '{genai_priority}', rule matrix says '{rule.priority}'")
    return mismatches


def validate_policy_reference(db: Session, doc_code: str) -> Optional[str]:
    """Returns an error string if the cited policy doesn't exist or isn't
    active; None if the citation checks out."""
    doc = db.query(PolicyDocument).filter_by(doc_code=doc_code).first()
    if not doc:
        return f"Policy '{doc_code}' does not exist in the knowledge base."
    if not doc.is_active:
        return f"Policy '{doc_code}' is superseded/inactive — citation is stale."
    return None


def validate_required_actions(rule: Optional[RuleMatrixEntry], genai_resolution_steps: List[str]) -> List[str]:
    """Returns any rule-mandated actions missing from GenAI's resolution_steps."""
    if not rule or not rule.required_actions:
        return []
    required = [a.strip().lower() for a in rule.required_actions.split(",") if a.strip()]
    steps_text = " ".join(genai_resolution_steps).lower()
    return [action for action in required if action not in steps_text]
