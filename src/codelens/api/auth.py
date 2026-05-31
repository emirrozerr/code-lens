"""Authentication endpoints — login, logout, me."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from jose import JWTError, jwt
from pydantic import BaseModel

from codelens.api import store
from codelens.api.deps import current_user
from codelens.settings import settings

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


def _make_token(user_id: str, email: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
    return jwt.encode(
        {"sub": user_id, "email": email, "role": role, "exp": exp},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def _user_dict(row: store.sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "role": row["role"],
        "createdAt": row["created_at"],
        "lastLogin": row["last_login"],
    }


@router.post("/auth/login")
def login(body: LoginRequest, response: Response):
    user = store.get_user_by_email(body.email)
    if not user or not store.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    store.update_last_login(user["id"])
    token = _make_token(user["id"], user["email"], user["role"])

    response.set_cookie(
        "codelens_token",
        token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expiry_minutes * 60,
    )
    return {"access_token": token, "token_type": "bearer", "user": _user_dict(user)}


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("codelens_token")
    return {"ok": True}


@router.get("/api/users/me")
def me(user=Depends(current_user)):
    return _user_dict(user)


@router.get("/auth/me")
def auth_me(authorization: str | None = Header(default=None)):
    """Called by the Next.js /api/auth/me route handler with Authorization: Bearer <token>."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _user_dict(user)
