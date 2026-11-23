"""
FastAPI dependencies for the current user + role gating. Cookie-based
(not just a bearer header) so the server-rendered dashboards in
src/templates/ can rely on the browser sending it automatically.
"""
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.security import decode_access_token
from database.models import User
from database.session import get_db


def get_current_user(access_token: str | None = Cookie(default=None),
                      db: Session = Depends(get_db)) -> User:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(access_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    user = db.query(User).filter_by(id=payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user


def require_role(*allowed_roles: str):
    """Usage: Depends(require_role('admin')) or Depends(require_role('admin', 'agent'))."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                 detail=f"Requires role: {', '.join(allowed_roles)}")
        return user
    return checker
