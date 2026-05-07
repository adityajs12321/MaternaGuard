"""Backend configuration utilities."""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./maternaguard.db")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def get_secret_key() -> str:
    return os.getenv("SECRET_KEY", "dev-only-secret-key")


def get_algorithm() -> str:
    return os.getenv("ALGORITHM", "HS256")


def get_access_token_expiry_minutes() -> int:
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


def get_model_path() -> Path:
    models_dir = repo_root() / "ml_new" / "models"
    rf_path = models_dir / "model_rf_v1.pkl"
    # For ensemble/hybrid mode, we want the RF path because it acts as the top of the hybrid model
    return Path(os.getenv("MODEL_PATH", str(rf_path))).resolve()


def get_scaler_path() -> Path:
    default_path = repo_root() / "ml_new" / "models" / "scaler.pkl"
    return Path(os.getenv("SCALER_PATH", str(default_path))).resolve()
