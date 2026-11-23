from typing import List, Optional
from pydantic import BaseModel, Field


class Mismatch(BaseModel):
    field: str
    genai_value: str
    expected_value: str
    severity: str = "medium"  # low | medium | high | critical


class ValidationOutcome(BaseModel):
    is_match: bool
    mismatches: List[Mismatch] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)  # e.g. unsupported_promise, missed_escalation
    corrected_department: Optional[str] = None
    corrected_escalate: Optional[bool] = None
    requires_manual_review: bool = False
    notes: str = ""
