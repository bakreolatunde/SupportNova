"""Produces one row of the GenAI-vs-Python Comparison Report per complaint —
the SRS requires 100+ of these across the dataset."""
from schemas.genai_output_schema import GenAIComplaintAnalysis
from schemas.validation_schema import ValidationOutcome


def build_comparison_row(complaint_id: str, analysis: GenAIComplaintAnalysis,
                          outcome: ValidationOutcome) -> dict:
    return {
        "complaint_id": complaint_id,
        "genai_department": ", ".join(analysis.departments),
        "expected_department": outcome.corrected_department or ", ".join(analysis.departments),
        "genai_urgency": analysis.urgency,
        "genai_priority": analysis.priority,
        "genai_escalate": analysis.escalate,
        "expected_escalate": outcome.corrected_escalate if outcome.corrected_escalate is not None else analysis.escalate,
        "match": outcome.is_match,
        "risk_flags": ", ".join(outcome.risk_flags),
        "requires_manual_review": outcome.requires_manual_review,
    }
