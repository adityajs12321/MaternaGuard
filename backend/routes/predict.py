"""Prediction route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Assessment, Patient
from ..schemas import AssessmentInput, AssessmentResult
from ..services.predictor import predictor
from ..services.shap_service import explain_action_message
from ..services.sms import send_referral_sms


router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=AssessmentResult)
def predict_assessment(payload: AssessmentInput, db: Session = Depends(get_db)) -> AssessmentResult:
    if not predictor.status.model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model unavailable: {predictor.status.details}",
        )

    result = predictor.predict(payload.model_dump())

    patient = None
    if payload.abha_id:
        patient = db.query(Patient).filter(Patient.abha_id == payload.abha_id).first()
        if not patient:
            patient = Patient(abha_id=payload.abha_id)
            db.add(patient)
            db.flush()

    assessment = Assessment(
        patient_id=patient.id if patient else None,
        abha_id=payload.abha_id,
        device_id=payload.device_id,
        age=payload.age,
        sbp=payload.sbp,
        dbp=payload.dbp,
        blood_sugar=payload.blood_sugar,
        body_temp=payload.body_temp,
        heart_rate=payload.heart_rate,
        risk_level=result["risk_level"],
        confidence=result["confidence"],
        top_feature=result["top_feature"],
        shap_values=result["shap_values"],
        source="online",
        original_timestamp=payload.original_timestamp,
        sms_sent=False,
    )
    db.add(assessment)
    db.flush()

    sms_sent = False
    if assessment.risk_level == "high":
        sms_sent = send_referral_sms(
            assessment.abha_id,
            assessment.risk_level,
            assessment.original_timestamp.isoformat(),
            assessment.device_id,
        )
        assessment.sms_sent = sms_sent

    db.commit()

    return AssessmentResult(
        risk_level=result["risk_level"],
        confidence=result["confidence"],
        top_feature=result["top_feature"],
        shap_values=result["shap_values"],
        message=explain_action_message(result["risk_level"], result["top_feature"]),
    )
