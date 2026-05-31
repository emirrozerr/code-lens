"""FastAPI dependency injection — JWT auth and admin guard."""

from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt

from codelens.settings import settings
from codelens.api import store
from codelens.api.store import Row


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def current_user(codelens_token: str | None = Cookie(default=None)) -> Row:
    if not codelens_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = _decode_token(codelens_token)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def admin_user(user=Depends(current_user)) -> Row:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
