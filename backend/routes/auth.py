"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..schemas import LoginRequest, TokenResponse
from ..security import create_access_token, validate_doctor_credentials


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if not validate_doctor_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return TokenResponse(access_token=create_access_token(payload.username))
