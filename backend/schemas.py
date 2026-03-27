"""Pydantic schemas for API requests/responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssessmentInput(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    abha_id: str | None = Field(default=None, max_length=20)
    age: float = Field(ge=10, le=60)
    sbp: float = Field(ge=70, le=220)
    dbp: float = Field(ge=40, le=140)
    blood_sugar: float = Field(ge=2.0, le=30.0)
    body_temp: float = Field(ge=34.0, le=43.0)
    heart_rate: float = Field(ge=30, le=200)
    original_timestamp: datetime


class AssessmentResult(BaseModel):
    risk_level: str
    confidence: float
    top_feature: str | None = None
    shap_values: dict | None = None
    message: str


class SyncRequest(BaseModel):
    assessments: list[AssessmentInput]


class SyncResponse(BaseModel):
    synced_count: int
    high_risk_count: int
    sms_sent: bool
    errors: list[str]


class PatientSummary(BaseModel):
    abha_id: str | None = None
    latest_device_id: str
    total_assessments: int
    latest_risk: str
    latest_date: datetime
    high_risk_count: int


class AssessmentHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: str
    abha_id: str | None = None
    age: float
    sbp: float
    dbp: float
    blood_sugar: float
    body_temp: float
    heart_rate: float
    risk_level: str
    confidence: float
    top_feature: str | None = None
    shap_values: dict | None = None
    source: str
    sms_sent: bool
    original_timestamp: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
