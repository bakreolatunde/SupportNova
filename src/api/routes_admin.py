from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.models import ReviewQueueItem
from database.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/review-queue")
def list_review_queue(db: Session = Depends(get_db)):
    items = db.query(ReviewQueueItem).filter_by(resolved=False).all()
    return [
        {"id": i.id, "complaint_id": i.complaint_id, "reason": i.reason, "created_at": i.created_at.isoformat()}
        for i in items
    ]
