"""User management endpoints (admin only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from codelens.api import store
from codelens.api.deps import admin_user, current_user

router = APIRouter(prefix="/api/users")


def _user_dict(row: store.sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "role": row["role"],
        "createdAt": row["created_at"],
        "lastLogin": row["last_login"],
    }


class AddUserRequest(BaseModel):
    email: str


class SetRoleRequest(BaseModel):
    role: str


@router.get("")
def list_users(_=Depends(admin_user)):
    return [_user_dict(u) for u in store.list_users()]


@router.post("", status_code=status.HTTP_201_CREATED)
def add_user(body: AddUserRequest, _=Depends(admin_user)):
    if store.get_user_by_email(body.email):
        raise HTTPException(status_code=409, detail=f"User {body.email} already exists")
    user, temp_password = store.create_user(body.email)
    return {"user": _user_dict(user), "temporaryPassword": temp_password}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, current=Depends(admin_user)):
    if user_id == current["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    if not store.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")


@router.patch("/{user_id}/role")
def set_role(user_id: str, body: SetRoleRequest, _=Depends(admin_user)):
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=422, detail="role must be 'admin' or 'user'")
    user = store.set_user_role(user_id, body.role)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_dict(user)


@router.post("/{user_id}/reset-password")
def reset_password(user_id: str, _=Depends(admin_user)):
    temp = store.reset_user_password(user_id)
    if temp is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"temporaryPassword": temp}
