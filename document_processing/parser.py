"""Handles customer-attached files on a complaint (receipts, screenshots-as-PDF, etc.)
— separate from knowledge_base.ingestion, which is for internal policy documents."""
from knowledge_base.ingestion import extract_text


def parse_attachment(file_path: str) -> str:
    try:
        return extract_text(file_path)
    except ValueError:
        return ""  # unsupported type — logged upstream, never silently guessed at
