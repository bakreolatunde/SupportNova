"""Pipeline 1 entry point: raw complaint text -> validated GenAIComplaintAnalysis.
This module never decides routing/escalation on its own authority — that
verdict belongs to python_validation.pipeline, which checks this output
against the rule matrix before anything is acted on."""
from sqlalchemy.orm import Session

from database.models import Complaint, GenAIAnalysis
from genai_pipeline.client import GenAIClient, load_prompt_template
from knowledge_base.chunking import retrieve_relevant_chunks
from schemas.genai_output_schema import GenAIComplaintAnalysis
from security.prompt_injection_guard import flag_suspicious_phrases, wrap_untrusted_input

PROMPT_VERSION = "complaint_analysis_v1"

# Mirrors GenAIComplaintAnalysis for the Anthropic tool-use JSON schema.
# Kept in one place so schema and prompt template can't silently drift apart.
ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "primary_issue": {"type": "string"},
        "secondary_issues": {"type": "array", "items": {"type": "string"}},
        "category": {"type": "string"},
        "subcategory": {"type": "string"},
        "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "very_negative"]},
        "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "entities": {"type": "array", "items": {"type": "string"}},
        "departments": {"type": "array", "items": {"type": "string"}},
        "policy_references": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "doc_code": {"type": "string"},
                    "section": {"type": "string"},
                    "relevance_note": {"type": "string"},
                },
                "required": ["doc_code"],
            },
        },
        "resolution_steps": {"type": "array", "items": {"type": "string"}},
        "escalate": {"type": "boolean"},
        "escalation_reason": {"type": "string"},
        "response_text": {"type": "string"},
        "follow_up_actions": {"type": "array", "items": {"type": "string"}},
        "agent_guidance": {"type": "string"},
        "clarification_needed": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["primary_issue", "category", "subcategory", "sentiment",
                 "urgency", "priority", "departments", "escalate", "response_text"],
}


def analyze_complaint(db: Session, complaint: Complaint) -> tuple[GenAIComplaintAnalysis, GenAIAnalysis]:
    suspicious = flag_suspicious_phrases(complaint.raw_text)  # logged, not blocking — Pipeline 2 checks the effect

    kb_chunks = retrieve_relevant_chunks(db, complaint.raw_text)
    kb_context = "\n---\n".join(kb_chunks) if kb_chunks else "No matching policy context found."

    template = load_prompt_template(PROMPT_VERSION)
    prompt = template.format(
        kb_context=kb_context,
        complaint_text=wrap_untrusted_input(complaint.raw_text),
    )

    client = GenAIClient()
    raw = client.complete_json(prompt, ANALYSIS_JSON_SCHEMA)
    analysis = GenAIComplaintAnalysis.model_validate(raw)

    record = GenAIAnalysis(
        complaint_id=complaint.id,
        prompt_version=PROMPT_VERSION,
        provider=client.settings.genai_provider,
        model="claude-sonnet-4-6",
        raw_json=analysis.model_dump_json(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    if suspicious:
        record_suspicious_flags(db, complaint.id, suspicious)  # defined in python_validation.pipeline

    return analysis, record


def record_suspicious_flags(db: Session, complaint_id: str, patterns: list[str]) -> None:
    # Kept as a hook here to avoid a circular import; python_validation.pipeline
    # is the module that actually persists/acts on these flags.
    pass
