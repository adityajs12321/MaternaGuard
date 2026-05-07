"""Model inference service — remote Lambda edition.

When LAMBDA_PREDICT_URL is set, prediction requests are forwarded to the
AWS Lambda function URL.  When unset, falls back to local model loading
(for development).
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np

from config import get_model_path, get_scaler_path


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

# If set, all predictions are forwarded to this Lambda function URL.
LAMBDA_PREDICT_URL = os.getenv("LAMBDA_PREDICT_URL", "")


@dataclass
class PredictorStatus:
    model_loaded: bool
    details: str


class Predictor:
    def __init__(self) -> None:
        self.rf_model = None
        self.svm_model = None
        self.xgb_model = None
        self.gbt_model = None
        self.ann_model = None
        self.extractor = None
        self.scaler = None
        self.explainer = None
        self._use_lambda = bool(LAMBDA_PREDICT_URL)
        if self._use_lambda:
            self.status = PredictorStatus(
                model_loaded=True,
                details=f"Remote Lambda inference via {LAMBDA_PREDICT_URL}",
            )
        else:
            self.status = PredictorStatus(model_loaded=False, details="Model not loaded")
            self._load_artifacts()

    # ------------------------------------------------------------------
    # Local model loading (development only)
    # ------------------------------------------------------------------

    def _load_artifacts(self) -> None:
        # Suppress TF logging
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
        try:
            import joblib
            import shap
            import tensorflow as tf
            from tensorflow import keras
        except ImportError as e:
            self.status = PredictorStatus(
                model_loaded=False,
                details=f"Missing ML dependencies: {e}. Please set LAMBDA_PREDICT_URL or install ML packages locally.",
            )
            return

        models_dir: Path = get_model_path().parent
        scaler_path: Path = get_scaler_path()

        # Paths for all ensemble components
        rf_path = models_dir / "model_rf_v1.pkl"
        svm_path = models_dir / "model_svm.pkl"
        xgb_path = models_dir / "model_xgb.pkl"
        gbt_path = models_dir / "model_gbt.pkl"
        ann_path = models_dir / "model_ann.keras"

        # Require core artifacts and treat GBT as optional to avoid hard startup failures
        # from environment-specific pickle incompatibilities.
        if not (rf_path.exists() and svm_path.exists() and xgb_path.exists() and ann_path.exists() and scaler_path.exists()):
            self.status = PredictorStatus(
                model_loaded=False,
                details=f"Missing core ensemble artifacts in {models_dir}",
            )
            return

        self.scaler = joblib.load(scaler_path)

        # Load all 5 models for the Full Ensemble
        self.rf_model = joblib.load(rf_path)
        self.svm_model = joblib.load(svm_path)
        self.xgb_model = joblib.load(xgb_path)
        self.gbt_model = None
        gbt_loaded = False
        if gbt_path.exists():
            try:
                self.gbt_model = joblib.load(gbt_path)
                gbt_loaded = True
            except Exception:
                self.gbt_model = None

        # Load ANN and construct feature extractor
        self.ann_model = keras.models.load_model(ann_path)
        self.extractor = keras.Model(inputs=self.ann_model.inputs, outputs=self.ann_model.layers[-2].output)

        # Explainer will use XGB for feature importance generation to keep it fast & standard 11-feature space
        try:
            self.explainer = shap.TreeExplainer(self.xgb_model)
        except Exception:
            self.explainer = None
        details = "Loaded voting Ensemble (RF, SVM, ANN, XGB"
        details += ", GBT)" if gbt_loaded else ") - GBT skipped due to artifact compatibility"
        if self.explainer is None:
            details += " - SHAP fallback enabled"
        self.status = PredictorStatus(model_loaded=True, details=details)

    # ------------------------------------------------------------------
    # Feature engineering (shared between local and remote)
    # ------------------------------------------------------------------

    def engineer_features(self, vitals: dict) -> np.ndarray:
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
                age,
                sbp,
                dbp,
                blood_sugar,
                body_temp,
                heart_rate,
                pulse_pressure,
                map_val,
                hyperglycemia_flag,
                age_band,
                bp_severity,
            ]]
        )

    # ------------------------------------------------------------------
    # Remote Lambda prediction
    # ------------------------------------------------------------------

    def _predict_remote(self, vitals: dict) -> dict:
        """Call the AWS Lambda function URL for prediction."""
        payload = json.dumps({
            "age": vitals["age"],
            "sbp": vitals["sbp"],
            "dbp": vitals["dbp"],
            "blood_sugar": vitals["blood_sugar"],
            "body_temp": vitals["body_temp"],
            "heart_rate": vitals["heart_rate"],
        }).encode("utf-8")

        req = urllib.request.Request(
            LAMBDA_PREDICT_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                # Lambda may wrap in a body field (API Gateway proxy response)
                if "body" in body and isinstance(body["body"], str):
                    return json.loads(body["body"])
                return body
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Lambda prediction failed ({exc.code}): {error_body}") from exc
        except Exception as exc:
            raise RuntimeError(f"Lambda prediction error: {exc}") from exc

    # ------------------------------------------------------------------
    # Local prediction
    # ------------------------------------------------------------------

    def _predict_local(self, vitals: dict) -> dict:
        """Run ensemble prediction locally using loaded models."""
        x_raw = self.engineer_features(vitals)
        x_scaled = self.scaler.transform(x_raw)

        # 1. Base inputs for XGB, GBT, and ANN
        xgb_proba = self.xgb_model.predict_proba(x_scaled)[0]
        ann_proba = self.ann_model.predict(x_scaled, verbose=0)[0]

        # 2. Extract latent features from ANN for Feature Fused models (RF, SVM)
        x_ann = self.extractor.predict(x_scaled, verbose=0)
        x_fused = np.concatenate([x_scaled, x_ann], axis=1)

        rf_proba = self.rf_model.predict_proba(x_fused)[0]
        svm_proba = self.svm_model.predict_proba(x_fused)[0]

        # 3. Ensemble Average (Soft Voting) since meta_svm was not saved by Member A's pipeline
        probas: List[np.ndarray] = [xgb_proba, ann_proba, rf_proba, svm_proba]
        if self.gbt_model is not None:
            probas.append(self.gbt_model.predict_proba(x_scaled)[0])
        ensemble_proba = np.mean(np.vstack(probas), axis=0)

        pred_idx = int(np.argmax(ensemble_proba))
        risk_level = LABEL_MAP[pred_idx]
        confidence = float(np.max(ensemble_proba))

        # 4. SHAP uses XGB for the clean 11-feature interpretability
        if self.explainer is not None:
            shap_values = self.explainer.shap_values(x_scaled)
            selected_shap = shap_values[pred_idx][0] if isinstance(shap_values, list) else shap_values[0, :, pred_idx]
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, vitals: dict) -> dict:
        if not self.status.model_loaded:
            raise RuntimeError(self.status.details)

        if self._use_lambda:
            return self._predict_remote(vitals)
        return self._predict_local(vitals)


predictor = Predictor()
