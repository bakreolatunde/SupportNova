"""
Shared submission flow — used by both the JSON API (routes_complaints) and
the HTML dashboard form (routes_dashboard), so there is exactly one place
that runs preprocessing -> Pipeline 1 -> Pipeline 2 -> review-queue routing.
"""
from sqlalchemy.orm import Session

from complaint_processing.preprocessing import clean_text, is_near_duplicate
from database.models import Complaint, ReviewQueueItem
from genai_pipeline.pipeline import analyze_complaint
from python_validation.pipeline import validate_analysis


def submit_complaint(db: Session, customer_email: str, raw_text: str) -> tuple[Complaint, str | None]:
    """Returns (complaint, error_message). error_message is set when Pipeline 1
    failed outright (still returns the saved complaint, routed to review)."""
    text = clean_text(raw_text)

    recent = db.query(Complaint).filter_by(customer_email=customer_email).all()
    duplicate = next((c for c in recent if is_near_duplicate(c.raw_text, text)), None)

    complaint = Complaint(customer_email=customer_email, raw_text=text,
                           is_duplicate_of=duplicate.id if duplicate else None)
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    try:
        analysis, analysis_record = analyze_complaint(db, complaint)
    except Exception as exc:  # noqa: BLE001
        complaint.status = "needs_review"
        db.add(ReviewQueueItem(complaint_id=complaint.id, reason=f"genai_pipeline_error: {exc}"))
        db.commit()
        return complaint, str(exc)

    outcome = validate_analysis(db, complaint, analysis, analysis_record, repeat_count=len(recent))
    complaint.status = "needs_review" if outcome.requires_manual_review else "validated"
    if outcome.requires_manual_review:
        reason = ", ".join(outcome.risk_flags) or "mismatch between GenAI output and rule matrix"
        db.add(ReviewQueueItem(complaint_id=complaint.id, reason=reason))
    db.commit()

    return complaint, None
