"""Simple, dependency-free chunking. Swap for a smarter splitter later —
the interface (list[str] in, KnowledgeChunk rows out) won't need to change."""
from typing import List
from sqlalchemy.orm import Session

from database.models import KnowledgeChunk


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[str]:
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def save_chunks(db: Session, document_id: str, chunks: List[str]) -> None:
    for i, chunk in enumerate(chunks):
        db.add(KnowledgeChunk(document_id=document_id, chunk_index=i, text=chunk))
    db.commit()


def retrieve_relevant_chunks(db: Session, query: str, top_k: int = 5) -> List[str]:
    """Placeholder retrieval: naive keyword overlap scoring.
    TODO: swap for embeddings + vector search once the KB grows past a
    handful of documents — the call signature below already supports it."""
    terms = set(w.lower() for w in query.split() if len(w) > 3)
    chunks = db.query(KnowledgeChunk).all()
    scored = []
    for c in chunks:
        text_lower = c.text.lower()
        score = sum(1 for t in terms if t in text_lower)
        if score:
            scored.append((score, c.text))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in scored[:top_k]]
