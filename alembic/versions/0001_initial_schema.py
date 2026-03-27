"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-27 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("abha_id", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patients_abha_id", "patients", ["abha_id"], unique=False)

    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=True),
        sa.Column("abha_id", sa.String(length=20), nullable=True),
        sa.Column("device_id", sa.String(length=64), nullable=False),
        sa.Column("age", sa.Float(), nullable=False),
        sa.Column("sbp", sa.Float(), nullable=False),
        sa.Column("dbp", sa.Float(), nullable=False),
        sa.Column("blood_sugar", sa.Float(), nullable=False),
        sa.Column("body_temp", sa.Float(), nullable=False),
        sa.Column("heart_rate", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=10), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("top_feature", sa.String(length=64), nullable=True),
        sa.Column("shap_values", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("sms_sent", sa.Boolean(), nullable=False),
        sa.Column("synced_at", sa.DateTime(), nullable=False),
        sa.Column("original_timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assessment_dedupe", "assessments", ["device_id", "original_timestamp"], unique=False)
    op.create_index("ix_assessments_abha_id", "assessments", ["abha_id"], unique=False)
    op.create_index("ix_assessments_device_id", "assessments", ["device_id"], unique=False)
    op.create_index("ix_assessments_original_timestamp", "assessments", ["original_timestamp"], unique=False)
    op.create_index("ix_assessments_risk_level", "assessments", ["risk_level"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_assessments_risk_level", table_name="assessments")
    op.drop_index("ix_assessments_original_timestamp", table_name="assessments")
    op.drop_index("ix_assessments_device_id", table_name="assessments")
    op.drop_index("ix_assessments_abha_id", table_name="assessments")
    op.drop_index("ix_assessment_dedupe", table_name="assessments")
    op.drop_table("assessments")
    op.drop_index("ix_patients_abha_id", table_name="patients")
    op.drop_table("patients")
