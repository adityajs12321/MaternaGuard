"""Shared constants for MaternaGuard ML pipeline."""

CORE_FEATURES = [
    "age",
    "sbp",
    "dbp",
    "blood_sugar",
    "body_temp",
    "heart_rate",
]

ENGINEERED_FEATURES = [
    "pulse_pressure",
    "map",
    "hyperglycemia_flag",
    "age_band",
    "bp_severity",
]

MODEL_FEATURES = CORE_FEATURES + ENGINEERED_FEATURES

RISK_LABELS = {
    0: "Low Risk",
    1: "Mid Risk",
    2: "High Risk",
}

OFFLINE_EXPLANATION_MAP = {
    "sbp": "Elevated systolic blood pressure is the primary concern",
    "dbp": "Elevated diastolic blood pressure is a concern",
    "blood_sugar": "High blood sugar indicates gestational diabetes risk",
    "pulse_pressure": "High pulse pressure may indicate preeclampsia",
    "bp_severity": "Hypertension detected, referral may be needed",
    "age_band": "Age is a contributing risk factor",
    "hyperglycemia_flag": "Blood sugar exceeds gestational diabetes threshold",
    "map": "Mean arterial pressure is elevated",
    "heart_rate": "Heart rate is outside normal range",
    "body_temp": "Body temperature suggests possible infection",
    "age": "Patient age contributes to risk profile",
}
