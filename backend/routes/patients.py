"""Doctor dashboard routes."""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..dependencies import get_db, require_doctor
from ..models import Assessment
from ..schemas import AssessmentHistoryItem, PatientSummary


router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientSummary])
def list_patients(
    risk_level: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _doctor: str = Depends(require_doctor),
    db: Session = Depends(get_db),
) -> list[PatientSummary]:
    query = db.query(Assessment)
    if risk_level:
        query = query.filter(Assessment.risk_level == risk_level)

    rows = query.order_by(desc(Assessment.original_timestamp)).all()
    grouped: dict[str, list[Assessment]] = defaultdict(list)
    for row in rows:
        key = row.abha_id or f"device:{row.device_id}"
        grouped[key].append(row)

    summaries: list[PatientSummary] = []
    for _, items in grouped.items():
        latest = items[0]
        high_risk_count = sum(1 for entry in items if entry.risk_level == "high")
        summaries.append(
            PatientSummary(
                abha_id=latest.abha_id,
                latest_device_id=latest.device_id,
                total_assessments=len(items),
                latest_risk=latest.risk_level,
                latest_date=latest.original_timestamp,
                high_risk_count=high_risk_count,
            )
        )

    summaries.sort(key=lambda item: item.latest_date, reverse=True)
    return summaries[offset : offset + limit]


@router.get("/{abha_id}/assessments", response_model=list[AssessmentHistoryItem])
def patient_assessments(
    abha_id: str,
    _doctor: str = Depends(require_doctor),
    db: Session = Depends(get_db),
) -> list[AssessmentHistoryItem]:
    rows = (
        db.query(Assessment)
        .filter(Assessment.abha_id == abha_id)
        .order_by(desc(Assessment.original_timestamp))
        .all()
    )
    return [AssessmentHistoryItem.model_validate(row) for row in rows]
