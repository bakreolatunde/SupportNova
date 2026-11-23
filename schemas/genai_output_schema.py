"""
The strict contract GenAI must return. Pipeline 1 validates the raw model
response against this before anything downstream touches it — a response
that doesn't parse is a retry or a manual-review case, never a guess.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class PolicyReference(BaseModel):
    doc_code: str
    section: Optional[str] = None
    relevance_note: str = ""


class GenAIComplaintAnalysis(BaseModel):
    primary_issue: str
    secondary_issues: List[str] = Field(default_factory=list)
    category: str
    subcategory: str
    sentiment: str          # positive | neutral | negative | very_negative
    urgency: str            # low | medium | high | critical  (kept separate from sentiment)
    priority: str            # low | medium | high | critical
    entities: List[str] = Field(default_factory=list)
    departments: List[str]
    policy_references: List[PolicyReference] = Field(default_factory=list)
    resolution_steps: List[str] = Field(default_factory=list)
    escalate: bool
    escalation_reason: Optional[str] = None
    response_text: str
    follow_up_actions: List[str] = Field(default_factory=list)
    agent_guidance: str = ""
    clarification_needed: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
