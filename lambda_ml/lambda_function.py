"""AWS Lambda handler for MaternaGuard ML inference.

Loads the ensemble of models (RF, SVM, XGB, GBT, ANN) from a Lambda layer
mounted at /opt/ml/models and returns predictions with SHAP explanations.
"""

from __future__ import annotations

import json
import os
import traceback
from pathlib import Path

# Suppress TF logging before importing
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import joblib
import numpy as np

# TensorFlow/Keras may or may not be available depending on layer setup.
# For Lambda, we try keras first, then fall back to tflite.
try:
    import tensorflow as tf
    from tensorflow import keras
    HAS_TF = True
except ImportError:
    HAS_TF = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


FEATURE_NAMES = [
    "age",
    "sbp",
    "dbp",
    "blood_sugar",
    "body_temp",
    "heart_rate",
    "pulse_pressure",
    "map",
    "hyperglycemia_flag",
    "age_band",
    "bp_severity",
]

LABEL_MAP = {0: "low", 1: "mid", 2: "high"}

# Models directory — either a Lambda layer path or local for testing
MODELS_DIR = Path(os.environ.get("MODELS_DIR", "/opt/ml/models"))

# Global model cache (warm starts reuse these)
_models = {}


def _load_models():
    """Load all model artifacts once and cache in module globals."""
    if _models.get("loaded"):
        return

    scaler_path = MODELS_DIR / "scaler.pkl"
    rf_path = MODELS_DIR / "model_rf_v1.pkl"
    svm_path = MODELS_DIR / "model_svm.pkl"
    xgb_path = MODELS_DIR / "model_xgb.pkl"
    gbt_path = MODELS_DIR / "model_gbt.pkl"
    ann_path = MODELS_DIR / "model_ann.keras"

    if not (rf_path.exists() and svm_path.exists() and xgb_path.exists() and scaler_path.exists()):
        raise RuntimeError(f"Missing core ensemble artifacts in {MODELS_DIR}")

    _models["scaler"] = joblib.load(scaler_path)
    _models["rf"] = joblib.load(rf_path)
    _models["svm"] = joblib.load(svm_path)
    _models["xgb"] = joblib.load(xgb_path)

    # GBT is optional
    _models["gbt"] = None
    if gbt_path.exists():
        try:
            _models["gbt"] = joblib.load(gbt_path)
        except Exception:
            _models["gbt"] = None

    # ANN
    _models["ann"] = None
    _models["extractor"] = None
    if HAS_TF and ann_path.exists():
        _models["ann"] = keras.models.load_model(ann_path)
        _models["extractor"] = keras.Model(
            inputs=_models["ann"].inputs,
            outputs=_models["ann"].layers[-2].output,
        )

    # SHAP explainer on XGB
    _models["explainer"] = None
    if HAS_SHAP:
        try:
            _models["explainer"] = shap.TreeExplainer(_models["xgb"])
        except Exception:
            _models["explainer"] = None

    _models["loaded"] = True


def engineer_features(vitals: dict) -> np.ndarray:
    """Compute engineered features from raw vitals."""
    age = vitals["age"]
    sbp = vitals["sbp"]
    dbp = vitals["dbp"]
    blood_sugar = vitals["blood_sugar"]
    body_temp = vitals["body_temp"]
    heart_rate = vitals["heart_rate"]

    pulse_pressure = sbp - dbp
    map_val = (sbp + 2.0 * dbp) / 3.0
    hyperglycemia_flag = 1.0 if blood_sugar > 7.8 else 0.0
    age_band = 2.0 if age < 20 else (1.0 if age > 35 else 0.0)
    bp_severity = 2.0 if sbp >= 160 else (1.0 if sbp >= 140 else 0.0)

    return np.array(
        [[
            age, sbp, dbp, blood_sugar, body_temp, heart_rate,
            pulse_pressure, map_val, hyperglycemia_flag, age_band, bp_severity,
        ]]
    )


def predict(vitals: dict) -> dict:
    """Run the full ensemble prediction pipeline."""
    _load_models()

    x_raw = engineer_features(vitals)
    x_scaled = _models["scaler"].transform(x_raw)

    # Collect probability vectors from each model
    xgb_proba = _models["xgb"].predict_proba(x_scaled)[0]
    probas = [xgb_proba]

    # ANN prediction + feature extraction for fused models
    if _models["ann"] is not None:
        ann_proba = _models["ann"].predict(x_scaled, verbose=0)[0]
        probas.append(ann_proba)

        x_ann = _models["extractor"].predict(x_scaled, verbose=0)
        x_fused = np.concatenate([x_scaled, x_ann], axis=1)
    else:
        x_fused = x_scaled

    rf_proba = _models["rf"].predict_proba(x_fused)[0]
    svm_proba = _models["svm"].predict_proba(x_fused)[0]
    probas.extend([rf_proba, svm_proba])

    if _models["gbt"] is not None:
        probas.append(_models["gbt"].predict_proba(x_scaled)[0])

    ensemble_proba = np.mean(np.vstack(probas), axis=0)
    pred_idx = int(np.argmax(ensemble_proba))
    risk_level = LABEL_MAP[pred_idx]
    confidence = float(np.max(ensemble_proba))

    # SHAP explanations
    if _models["explainer"] is not None:
        shap_values = _models["explainer"].shap_values(x_scaled)
        selected_shap = (
            shap_values[pred_idx][0]
            if isinstance(shap_values, list)
            else shap_values[0, :, pred_idx]
        )
        top_idx = int(np.argmax(np.abs(selected_shap)))
        top_feature = FEATURE_NAMES[top_idx]
        shap_dict = {name: float(val) for name, val in zip(FEATURE_NAMES, selected_shap)}
    else:
        top_feature = FEATURE_NAMES[0]
        shap_dict = {name: 0.0 for name in FEATURE_NAMES}

    return {
        "risk_level": risk_level,
        "confidence": confidence,
        "top_feature": top_feature,
        "shap_values": shap_dict,
    }


def lambda_handler(event, context):
    """AWS Lambda entry point.

    Accepts either:
      - API Gateway proxy event (body is JSON string)
      - Direct invocation (event is the vitals dict)
    """
    try:
        # Parse body from API Gateway or direct invocation
        if "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        vitals = {
            "age": float(body["age"]),
            "sbp": float(body["sbp"]),
            "dbp": float(body["dbp"]),
            "blood_sugar": float(body["blood_sugar"]),
            "body_temp": float(body["body_temp"]),
            "heart_rate": float(body["heart_rate"]),
        }

        result = predict(vitals)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(result),
        }

    except Exception as exc:
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(exc)}),
        }
