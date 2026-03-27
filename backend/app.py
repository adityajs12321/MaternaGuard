"""FastAPI app entry point."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .database import Base, SessionLocal, engine
from .routes import assessments, auth, patients, predict, sync
from .services.predictor import predictor


app = FastAPI(title="MaternaGuard Backend", version="1.0.0")

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(sync.router)
app.include_router(patients.router)
app.include_router(assessments.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    db_connected = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False
    finally:
        try:
            db.close()
        except Exception:
            pass

    return {
        "status": "ok",
        "model_loaded": predictor.status.model_loaded,
        "db_connected": db_connected,
        "model_details": predictor.status.details,
    }
