"""Assessment retrieval routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from dependencies import get_db, require_doctor
from models import Assessment
from schemas import AssessmentHistoryItem


router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/device/{device_id}", response_model=list[AssessmentHistoryItem])
def list_device_assessments(
    device_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[AssessmentHistoryItem]:
    rows = (
        db.query(Assessment)
        .filter(Assessment.device_id == device_id)
        .order_by(desc(Assessment.original_timestamp))
        .limit(limit)
        .all()
    )
    return [AssessmentHistoryItem.model_validate(row) for row in rows]


@router.get("/provider/device/{device_id}", response_model=list[AssessmentHistoryItem])
def provider_device_assessments(
    device_id: str,
    _doctor: str = Depends(require_doctor),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[AssessmentHistoryItem]:
    rows = (
        db.query(Assessment)
        .filter(Assessment.device_id == device_id)
        .order_by(desc(Assessment.original_timestamp))
        .limit(limit)
        .all()
    )
    return [AssessmentHistoryItem.model_validate(row) for row in rows]
