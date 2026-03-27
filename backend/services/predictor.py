"""Model inference and SHAP service wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import os
import joblib
import numpy as np
import shap

# Suppress TF logging
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import tensorflow as tf
from tensorflow import keras

from ..config import get_model_path, get_scaler_path


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
        self.status = PredictorStatus(model_loaded=False, details="Model not loaded")
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        models_dir: Path = get_model_path().parent
        scaler_path: Path = get_scaler_path()
        
        # Paths for all ensemble components
        rf_path = models_dir / "model_rf_v1.pkl"
        svm_path = models_dir / "model_svm.pkl"
        xgb_path = models_dir / "model_xgb.pkl"
        gbt_path = models_dir / "model_gbt.pkl"
        ann_path = models_dir / "model_ann.keras"

        if not (rf_path.exists() and svm_path.exists() and xgb_path.exists() and gbt_path.exists() and ann_path.exists() and scaler_path.exists()):
            self.status = PredictorStatus(
                model_loaded=False,
                details=f"Missing ensemble artifacts in {models_dir}",
            )
            return

        self.scaler = joblib.load(scaler_path)
        
        # Load all 5 models for the Full Ensemble
        self.rf_model = joblib.load(rf_path)
        self.svm_model = joblib.load(svm_path)
        self.xgb_model = joblib.load(xgb_path)
        self.gbt_model = joblib.load(gbt_path)
        
        # Load ANN and construct feature extractor
        self.ann_model = keras.models.load_model(ann_path)
        self.extractor = keras.Model(inputs=self.ann_model.inputs, outputs=self.ann_model.layers[-2].output)

        # Explainer will use XGB for feature importance generation to keep it fast & standard 11-feature space
        self.explainer = shap.TreeExplainer(self.xgb_model)
        self.status = PredictorStatus(model_loaded=True, details="Loaded full voting Ensemble (RF, SVM, ANN, XGB, GBT)")

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

    def predict(self, vitals: dict) -> dict:
        if not self.status.model_loaded:
            raise RuntimeError(self.status.details)

        x_raw = self.engineer_features(vitals)
        x_scaled = self.scaler.transform(x_raw)
        
        # 1. Base inputs for XGB, GBT, and ANN
        xgb_proba = self.xgb_model.predict_proba(x_scaled)[0]
        gbt_proba = self.gbt_model.predict_proba(x_scaled)[0]
        ann_proba = self.ann_model.predict(x_scaled, verbose=0)[0]
        
        # 2. Extract latent features from ANN for Feature Fused models (RF, SVM)
        x_ann = self.extractor.predict(x_scaled, verbose=0)
        x_fused = np.concatenate([x_scaled, x_ann], axis=1)
        
        rf_proba = self.rf_model.predict_proba(x_fused)[0]
        svm_proba = self.svm_model.predict_proba(x_fused)[0]
        
        # 3. Ensemble Average (Soft Voting) since meta_svm was not saved by Member A's pipeline
        ensemble_proba = (xgb_proba + gbt_proba + ann_proba + rf_proba + svm_proba) / 5.0

        pred_idx = int(np.argmax(ensemble_proba))
        risk_level = LABEL_MAP[pred_idx]
        confidence = float(np.max(ensemble_proba))

        # 4. SHAP uses XGB for the clean 11-feature interpretability
        shap_values = self.explainer.shap_values(x_scaled)
        selected_shap = shap_values[pred_idx][0] if isinstance(shap_values, list) else shap_values[0, :, pred_idx]
        
        top_idx = int(np.argmax(np.abs(selected_shap)))
        top_feature = FEATURE_NAMES[top_idx]
        shap_dict = {name: float(val) for name, val in zip(FEATURE_NAMES, selected_shap)}

        return {
            "risk_level": risk_level,
            "confidence": confidence,
            "top_feature": top_feature,
            "shap_values": shap_dict,
        }


predictor = Predictor()
