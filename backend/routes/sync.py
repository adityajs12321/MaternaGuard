"""Offline sync route."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Assessment, Patient
from ..schemas import SyncRequest, SyncResponse
from ..services.predictor import predictor
from ..services.sms import send_referral_sms


router = APIRouter(tags=["sync"])


@router.post("/sync", response_model=SyncResponse)
def sync_assessments(payload: SyncRequest, db: Session = Depends(get_db)) -> SyncResponse:
    if not payload.assessments:
        return SyncResponse(synced_count=0, high_risk_count=0, sms_sent=False, errors=[])

    errors: list[str] = []
    synced_count = 0
    high_risk_count = 0
    sms_sent_any = False

    for index, item in enumerate(payload.assessments):
        try:
            existing = (
                db.query(Assessment)
                .filter(
                    and_(
                        Assessment.device_id == item.device_id,
                        Assessment.original_timestamp == item.original_timestamp,
                    )
                )
                .first()
            )
            if existing:
                continue

            patient = None
            if item.abha_id:
                patient = db.query(Patient).filter(Patient.abha_id == item.abha_id).first()
                if not patient:
                    patient = Patient(abha_id=item.abha_id)
                    db.add(patient)
                    db.flush()

            result = predictor.predict(item.model_dump()) if predictor.status.model_loaded else {
                "risk_level": "mid",
                "confidence": 0.5,
                "top_feature": None,
                "shap_values": None,
            }

            assessment = Assessment(
                patient_id=patient.id if patient else None,
                abha_id=item.abha_id,
                device_id=item.device_id,
                age=item.age,
                sbp=item.sbp,
                dbp=item.dbp,
                blood_sugar=item.blood_sugar,
                body_temp=item.body_temp,
                heart_rate=item.heart_rate,
                risk_level=result["risk_level"],
                confidence=result["confidence"],
                top_feature=result["top_feature"],
                shap_values=result["shap_values"],
                source="device",
                original_timestamp=item.original_timestamp,
                sms_sent=False,
            )
            db.add(assessment)
            db.flush()

            if assessment.risk_level == "high":
                high_risk_count += 1
                sent = send_referral_sms(
                    assessment.abha_id,
                    assessment.risk_level,
                    assessment.original_timestamp.isoformat(),
                    assessment.device_id,
                )
                assessment.sms_sent = sent
                sms_sent_any = sms_sent_any or sent

            synced_count += 1
        except Exception as exc:
            errors.append(f"assessment[{index}] failed: {exc}")

    db.commit()
    return SyncResponse(
        synced_count=synced_count,
        high_risk_count=high_risk_count,
        sms_sent=sms_sent_any,
        errors=errors,
    )
