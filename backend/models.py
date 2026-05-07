"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    abha_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    assessments = relationship("Assessment", back_populates="patient")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"), nullable=True)
    abha_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    age: Mapped[float] = mapped_column(Float, nullable=False)
    sbp: Mapped[float] = mapped_column(Float, nullable=False)
    dbp: Mapped[float] = mapped_column(Float, nullable=False)
    blood_sugar: Mapped[float] = mapped_column(Float, nullable=False)
    body_temp: Mapped[float] = mapped_column(Float, nullable=False)
    heart_rate: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    top_feature: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shap_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(10), default="device", nullable=False)
    sms_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    original_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    patient = relationship("Patient", back_populates="assessments")


Index("ix_assessment_dedupe", Assessment.device_id, Assessment.original_timestamp)
