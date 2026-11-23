from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json

from database.models import Complaint, GenAIAnalysis, ValidationResult
from database.session import get_db
from src.api.complaint_service import submit_complaint

router = APIRouter(prefix="/complaints", tags=["complaints"])


class ComplaintIn(BaseModel):
    customer_email: str
    text: str


@router.post("")
def submit_complaint_endpoint(payload: ComplaintIn, db: Session = Depends(get_db)):
    complaint, error = submit_complaint(db, payload.customer_email, payload.text)
    if error:
        raise HTTPException(status_code=502, detail=f"GenAI analysis failed, routed to manual review: {error}")

    analysis_record = (db.query(GenAIAnalysis).filter_by(complaint_id=complaint.id)
                        .order_by(GenAIAnalysis.created_at.desc()).first())
    outcome_record = (db.query(ValidationResult).filter_by(complaint_id=complaint.id)
                       .order_by(ValidationResult.created_at.desc()).first())

    return {
        "complaint_id": complaint.id,
        "status": complaint.status,
        "genai_analysis": json.loads(analysis_record.raw_json) if analysis_record else None,
        "requires_manual_review": outcome_record.requires_manual_review if outcome_record else None,
        "risk_flags": outcome_record.risk_flags_json if outcome_record else None,
    }


@router.get("/{complaint_id}")
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter_by(id=complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {
        "id": complaint.id,
        "status": complaint.status,
        "raw_text": complaint.raw_text,
        "submitted_at": complaint.submitted_at.isoformat(),
    }
