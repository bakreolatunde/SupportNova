"""
Pipeline 2 entry point. Takes Pipeline 1's structured output and returns an
independent ValidationOutcome — this is the module competition evaluators
will probe hardest, so every check here must be explainable without
reference to any GenAI call.
"""
from sqlalchemy.orm import Session

from database.models import Complaint, GenAIAnalysis, RuleMatrixEntry, ValidationResult
from python_validation.escalation_checker import independent_escalation_check
from python_validation.hallucination_checker import find_unsupported_promises
from python_validation.rule_matrix_loader import find_rule
from python_validation.validators import (validate_department, validate_urgency_priority,
                                           validate_policy_reference, validate_required_actions)
from schemas.genai_output_schema import GenAIComplaintAnalysis
from schemas.validation_schema import Mismatch, ValidationOutcome


def validate_analysis(db: Session, complaint: Complaint, analysis: GenAIComplaintAnalysis,
                       analysis_record: GenAIAnalysis, policy_texts: list[str] | None = None,
                       repeat_count: int = 0) -> ValidationOutcome:
    mismatches: list[Mismatch] = []
    risk_flags: list[str] = []

    rule: RuleMatrixEntry | None = find_rule(db, analysis.category, analysis.subcategory)
    if rule is None:
        risk_flags.append("no_rule_matrix_entry")  # new/unseen category — always goes to manual review

    corrected_department = validate_department(analysis.departments, rule)
    if corrected_department:
        mismatches.append(Mismatch(
            field="department", genai_value=", ".join(analysis.departments),
            expected_value=corrected_department, severity="high",
        ))

    for m in validate_urgency_priority(analysis.urgency, analysis.priority, rule):
        mismatches.append(Mismatch(field="urgency_priority", genai_value=m, expected_value="", severity="medium"))

    for ref in analysis.policy_references:
        error = validate_policy_reference(db, ref.doc_code)
        if error:
            risk_flags.append("invalid_policy_reference")
            mismatches.append(Mismatch(field="policy_reference", genai_value=ref.doc_code,
                                        expected_value=error, severity="critical"))

    missing_actions = validate_required_actions(rule, analysis.resolution_steps)
    if missing_actions:
        risk_flags.append("missing_required_actions")
        mismatches.append(Mismatch(field="resolution_steps", genai_value="incomplete",
                                    expected_value=", ".join(missing_actions), severity="high"))

    should_escalate, escalation_reason = independent_escalation_check(
        complaint.raw_text, rule.must_escalate if rule else False, repeat_count,
    )
    corrected_escalate = None
    if should_escalate != analysis.escalate:
        corrected_escalate = should_escalate
        severity = "critical" if should_escalate and not analysis.escalate else "medium"
        mismatches.append(Mismatch(field="escalate", genai_value=str(analysis.escalate),
                                    expected_value=f"{should_escalate} ({escalation_reason})", severity=severity))
        if should_escalate and not analysis.escalate:
            risk_flags.append("missed_escalation")

    unsupported = find_unsupported_promises(analysis.response_text, policy_texts or [])
    if unsupported:
        risk_flags.append("unsupported_promise")
        mismatches.append(Mismatch(field="response_text", genai_value="; ".join(unsupported),
                                    expected_value="no unsupported promise", severity="critical"))

    critical_present = any(m.severity == "critical" for m in mismatches)
    requires_manual_review = critical_present or "no_rule_matrix_entry" in risk_flags

    outcome = ValidationOutcome(
        is_match=len(mismatches) == 0,
        mismatches=mismatches,
        risk_flags=risk_flags,
        corrected_department=corrected_department,
        corrected_escalate=corrected_escalate,
        requires_manual_review=requires_manual_review,
    )

    db.add(ValidationResult(
        complaint_id=complaint.id,
        analysis_id=analysis_record.id,
        is_match=outcome.is_match,
        mismatches_json=outcome.model_dump_json(include={"mismatches"}),
        risk_flags_json=str(outcome.risk_flags),
        corrected_department=outcome.corrected_department,
        corrected_escalate=outcome.corrected_escalate,
        requires_manual_review=outcome.requires_manual_review,
    ))
    db.commit()

    return outcome
