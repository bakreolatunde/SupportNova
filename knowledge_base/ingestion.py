"""
Turns uploaded policy PDFs/DOCX into plain text + a PolicyDocument row.
Versioning: re-uploading the same doc_code creates a new PolicyDocument
row with is_active flipped on the old one, never an in-place overwrite —
so the audit trail always shows what a past response was grounded in.
"""
from datetime import datetime

from pypdf import PdfReader
from docx import Document as DocxDocument
from sqlalchemy.orm import Session

from database.models import PolicyDocument
from knowledge_base.chunking import chunk_text, save_chunks


def extract_text(file_path: str) -> str:
    if file_path.lower().endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if file_path.lower().endswith(".docx"):
        doc = DocxDocument(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Unsupported document type: {file_path}")


def ingest_document(db: Session, file_path: str, doc_code: str, title: str,
                     version: str = "1.0") -> PolicyDocument:
    text = extract_text(file_path)

    existing = db.query(PolicyDocument).filter_by(doc_code=doc_code, is_active=True).first()
    if existing:
        existing.is_active = False

    record = PolicyDocument(
        doc_code=doc_code,
        title=title,
        version=version,
        effective_date=datetime.utcnow(),
        is_active=True,
        source_path=file_path,
        full_text=text,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    save_chunks(db, record.id, chunk_text(text))
    return record
