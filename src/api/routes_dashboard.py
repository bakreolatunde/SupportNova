from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_role
from auth.security import create_access_token, hash_password, verify_password
from database.models import Complaint, PolicyDocument, ReviewQueueItem, RuleMatrixEntry, User, UserRole
from database.session import get_db
from src.api.complaint_service import submit_complaint

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="src/templates")

ROLE_HOME = {"customer": "/dashboard/customer", "agent": "/dashboard/agent", "admin": "/dashboard/admin"}


@router.get("/login-page")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"user": None})


@router.post("/login-page")
def login_page_submit(request: Request, email: str = Form(...), password: str = Form(...),
                       db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request, "login.html", {"user": None,
                                                                    "error": "Invalid email or password"})

    token = create_access_token(subject=user.id, role=user.role.value)
    redirect = RedirectResponse(url=ROLE_HOME[user.role.value], status_code=303)
    redirect.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=60 * 60 * 8)
    return redirect


@router.get("/register-page")
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"user": None})


@router.post("/register-page")
def register_page_submit(request: Request, email: str = Form(...), password: str = Form(...),
                          role: str = Form("customer"), db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=email).first():
        return templates.TemplateResponse(request, "register.html",
                                           {"user": None, "error": "That email is already registered."})

    user = User(email=email, hashed_password=hash_password(password), role=UserRole(role))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role.value)
    redirect = RedirectResponse(url=ROLE_HOME[user.role.value], status_code=303)
    redirect.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=60 * 60 * 8)
    return redirect


@router.get("/logout-page")
def logout_page():
    redirect = RedirectResponse(url="/login-page", status_code=303)
    redirect.delete_cookie("access_token")
    return redirect


@router.get("/dashboard/customer")
def customer_dashboard(request: Request, user: User = Depends(require_role("customer")),
                        db: Session = Depends(get_db), submitted: int = 0, needs_review: int = 0):
    complaints = (db.query(Complaint).filter_by(customer_email=user.email)
                  .order_by(Complaint.submitted_at.desc()).all())
    return templates.TemplateResponse(request, "customer_dashboard.html",
                                       {"user": user, "complaints": complaints,
                                        "submitted": bool(submitted), "needs_review": bool(needs_review)})


@router.post("/dashboard/customer/submit")
def customer_submit(request: Request, text: str = Form(...),
                     user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    complaint, error = submit_complaint(db, user.email, text)
    needs_review = 1 if (error or complaint.status == "needs_review") else 0
    return RedirectResponse(url=f"/dashboard/customer?submitted=1&needs_review={needs_review}", status_code=303)


@router.get("/dashboard/agent")
def agent_dashboard(request: Request, user: User = Depends(require_role("agent", "admin")),
                     db: Session = Depends(get_db)):
    queue = (db.query(ReviewQueueItem).filter_by(resolved=False)
             .order_by(ReviewQueueItem.created_at.desc()).all())
    return templates.TemplateResponse(request, "agent_dashboard.html", {"user": user, "queue": queue})


@router.post("/dashboard/agent/resolve/{item_id}")
def resolve_review_item(item_id: str, user: User = Depends(require_role("agent", "admin")),
                         db: Session = Depends(get_db)):
    item = db.query(ReviewQueueItem).filter_by(id=item_id).first()
    if item:
        item.resolved = True
        db.commit()
    return RedirectResponse(url="/dashboard/agent", status_code=303)


@router.get("/dashboard/admin")
def admin_dashboard(request: Request, user: User = Depends(require_role("admin")),
                     db: Session = Depends(get_db)):
    total = db.query(Complaint).count()
    needs_review = db.query(Complaint).filter_by(status="needs_review").count()
    validated = db.query(Complaint).filter_by(status="validated").count()
    escalated = db.query(ReviewQueueItem).count()
    rule_rows = db.query(RuleMatrixEntry).count()
    active_policies = db.query(PolicyDocument).filter_by(is_active=True).count()
    recent = db.query(Complaint).order_by(Complaint.submitted_at.desc()).limit(20).all()

    stats = {"total_complaints": total, "needs_review": needs_review, "validated": validated,
             "escalated": escalated, "rule_matrix_rows": rule_rows, "active_policies": active_policies}
    return templates.TemplateResponse(request, "admin_dashboard.html", {"user": user, "stats": stats, "recent": recent})
