"""FastAPI dependencies (current user, role gates)."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise cred_exc from exc
    email = payload.get("sub")
    if not email:
        raise cred_exc
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise cred_exc
    return user


def require_hod(user: User = Depends(get_current_user)) -> User:
    if user.role != "hod":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HOD privileges required",
        )
    return user
