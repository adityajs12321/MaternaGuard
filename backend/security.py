"""Auth and JWT helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import get_access_token_expiry_minutes, get_algorithm, get_secret_key


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=get_access_token_expiry_minutes())
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, get_secret_key(), algorithm=get_algorithm())


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_secret_key(), algorithms=[get_algorithm()])


def validate_doctor_credentials(username: str, password: str) -> bool:
    env_user = os.getenv("DOCTOR_USERNAME", "doctor")
    env_password = os.getenv("DOCTOR_PASSWORD", "doctor123")

    if username != env_user:
        return False

    # Supports hashed passwords and plain text for local MVP.
    if env_password.startswith("$2"):
        return verify_password(password, env_password)
    return password == env_password


def is_token_valid(token: str) -> bool:
    try:
        payload = decode_token(token)
        return bool(payload.get("sub"))
    except JWTError:
        return False
