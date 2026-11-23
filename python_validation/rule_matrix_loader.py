from typing import Optional
from sqlalchemy.orm import Session

from database.models import RuleMatrixEntry


def find_rule(db: Session, category: str, subcategory: str) -> Optional[RuleMatrixEntry]:
    return (
        db.query(RuleMatrixEntry)
        .filter(RuleMatrixEntry.category.ilike(category), RuleMatrixEntry.subcategory.ilike(subcategory))
        .first()
    )


def load_rules_from_csv(db: Session, csv_path: str) -> int:
    """Bulk-loads the hand-authored rule matrix. Idempotent-ish: intended for
    initial load / admin re-sync, not called from the request path."""
    import csv as csv_module

    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv_module.DictReader(f):
            db.add(RuleMatrixEntry(
                category=row["category"],
                subcategory=row["subcategory"],
                condition_description=row.get("condition_description", ""),
                department=row["department"],
                urgency=row["urgency"],
                priority=row["priority"],
                policy_doc_code=row.get("policy_doc_code") or None,
                must_escalate=row.get("must_escalate", "false").lower() == "true",
                required_actions=row.get("required_actions", ""),
                prohibited_actions=row.get("prohibited_actions", ""),
            ))
            count += 1
    db.commit()
    return count


def sync_policy_documents_from_rule_matrix(db: Session, csv_path: str) -> int:
    """Ensures a PolicyDocument row exists (active) for every policy_doc_code
    referenced in the rule matrix, so policy-reference validation has real
    documents to check against. Real ingestion (knowledge_base.ingestion)
    replaces a placeholder the moment the actual policy PDF/DOCX is uploaded —
    this only fills gaps, never overwrites an already-ingested document."""
    import csv as csv_module
    from database.models import PolicyDocument

    codes = set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv_module.DictReader(f):
            code = row.get("policy_doc_code")
            if code:
                codes.add(code)

    created = 0
    for code in codes:
        exists = db.query(PolicyDocument).filter_by(doc_code=code, is_active=True).first()
        if not exists:
            db.add(PolicyDocument(doc_code=code, title=code.replace("-", " ").title(),
                                   version="1.0", is_active=True,
                                   full_text=f"Placeholder policy text for {code} — replace with real ingested document."))
            created += 1
    db.commit()
    return created
