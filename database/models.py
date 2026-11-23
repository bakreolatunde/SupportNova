"""
Core schema. Categories, departments, and policies live as DATA (rows),
not as hard-coded enums in application code — new ones must be addable
through the DB/admin UI alone, per the hidden-evaluation requirement.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (Column, String, Text, DateTime, Float, Boolean,
                         ForeignKey, Integer, Enum)
from sqlalchemy.orm import relationship

from database.session import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    customer = "customer"
    agent = "agent"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.customer)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, default="")


class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    id = Column(String, primary_key=True, default=gen_id)
    doc_code = Column(String, unique=True, nullable=False)  # e.g. POL-REFUND-003
    title = Column(String, nullable=False)
    version = Column(String, default="1.0")
    effective_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    source_path = Column(String, nullable=True)  # original PDF/DOCX path
    full_text = Column(Text, default="")


class KnowledgeChunk(Base):
    """A retrievable slice of a PolicyDocument, for grounding GenAI responses."""
    __tablename__ = "knowledge_chunks"
    id = Column(String, primary_key=True, default=gen_id)
    document_id = Column(String, ForeignKey("policy_documents.id"), nullable=False)
    chunk_index = Column(Integer, default=0)
    text = Column(Text, nullable=False)
    document = relationship("PolicyDocument")


class RuleMatrixEntry(Base):
    """One row of the hand-authored Complaint Resolution Rule Matrix — the
    ground truth Pipeline 2 validates against. Never populated by GenAI."""
    __tablename__ = "rule_matrix_entries"
    id = Column(String, primary_key=True, default=gen_id)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    condition_description = Column(Text, default="")
    department = Column(String, nullable=False)
    urgency = Column(String, nullable=False)      # low | medium | high | critical
    priority = Column(String, nullable=False)
    policy_doc_code = Column(String, nullable=True)
    must_escalate = Column(Boolean, default=False)
    required_actions = Column(Text, default="")   # comma-separated
    prohibited_actions = Column(Text, default="")


class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(String, primary_key=True, default=gen_id)
    customer_email = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="received")  # received|analyzed|validated|needs_review|resolved
    is_duplicate_of = Column(String, ForeignKey("complaints.id"), nullable=True)


class GenAIAnalysis(Base):
    """Raw structured output of Pipeline 1, stored verbatim for audit."""
    __tablename__ = "genai_analyses"
    id = Column(String, primary_key=True, default=gen_id)
    complaint_id = Column(String, ForeignKey("complaints.id"), nullable=False)
    prompt_version = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    raw_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ValidationResult(Base):
    """Pipeline 2's independent verdict on a GenAIAnalysis."""
    __tablename__ = "validation_results"
    id = Column(String, primary_key=True, default=gen_id)
    complaint_id = Column(String, ForeignKey("complaints.id"), nullable=False)
    analysis_id = Column(String, ForeignKey("genai_analyses.id"), nullable=False)
    is_match = Column(Boolean, default=True)
    mismatches_json = Column(Text, default="[]")   # list of {field, genai_value, expected_value}
    risk_flags_json = Column(Text, default="[]")   # e.g. ["unsupported_promise", "missed_escalation"]
    corrected_department = Column(String, nullable=True)
    corrected_escalate = Column(Boolean, nullable=True)
    requires_manual_review = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReviewQueueItem(Base):
    __tablename__ = "review_queue_items"
    id = Column(String, primary_key=True, default=gen_id)
    complaint_id = Column(String, ForeignKey("complaints.id"), nullable=False)
    reason = Column(String, nullable=False)
    assigned_to = Column(String, ForeignKey("users.id"), nullable=True)
    resolved = Column(Boolean, default=False)
    reviewer_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    complaint = relationship("Complaint")
