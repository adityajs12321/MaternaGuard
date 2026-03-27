"""Data loading, harmonization, and preprocessing utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import ADASYN
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from .constants import CORE_FEATURES, MODEL_FEATURES


def normalize_label(label: object) -> float:
    """Map raw risk labels to 3-class integer encoding."""
    if pd.isna(label):
        return np.nan
    text = str(label).strip().lower().replace("-", " ").replace("_", " ")
    text = " ".join(text.split())
    if text == "nan":
        return np.nan
    mapping = {
        "low risk": 0.0,
        "low": 0.0,
        "non high": np.nan,  # Fix label noise by ignoring ambiguous non-high labels
        "nonhigh": np.nan,   # from DS2/DS3 and only utilizing their confirmed High-risk cases
        "mid risk": 1.0,
        "mid": 1.0,
        "high risk": 2.0,
        "high": 2.0,
    }
    if text not in mapping:
        raise ValueError(f"Unknown label encountered: {label}")
    return mapping[text]


def _find_column(df: pd.DataFrame, aliases: list[str], required: bool = True) -> str | None:
    for alias in aliases:
        if alias in df.columns:
            return alias
    if required:
        raise KeyError(f"Missing required column. Tried aliases: {aliases}")
    return None


def _convert_temp_to_celsius_if_needed(df: pd.DataFrame, col_name: str = "body_temp") -> pd.DataFrame:
    if col_name in df.columns and df[col_name].notna().any():
        mean_temp = df[col_name].astype(float).mean()
        if mean_temp > 50:
            df[col_name] = (df[col_name].astype(float) - 32.0) * 5.0 / 9.0
    return df


def inspect_dataset(df: pd.DataFrame, name: str, target_col: str = "RiskLevel") -> Dict[str, object]:
    """Return inspection details requested in prompt."""
    target_name = target_col if target_col in df.columns else "risk_level"
    body_temp_col = "BodyTemp" if "BodyTemp" in df.columns else "body_temp"

    return {
        "name": name,
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
        "null_counts": df.isna().sum().to_dict(),
        "target_counts": df[target_name].value_counts(dropna=False).to_dict() if target_name in df.columns else {},
        "body_temp_mean": float(df[body_temp_col].mean()) if body_temp_col in df.columns else None,
    }


def _standardize_ds1(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["age"] = df[_find_column(df, ["Age"])].astype(float)
    out["sbp"] = df[_find_column(df, ["SystolicBP"])].astype(float)
    out["dbp"] = df[_find_column(df, ["DiastolicBP"])].astype(float)
    out["blood_sugar"] = df[_find_column(df, ["BS", "BloodSugar"])].astype(float)
    out["body_temp"] = df[_find_column(df, ["BodyTemp"])].astype(float)
    out["heart_rate"] = df[_find_column(df, ["HeartRate"])].astype(float)
    out["risk_level"] = df[_find_column(df, ["RiskLevel"])].apply(normalize_label)
    return _convert_temp_to_celsius_if_needed(out)


def _standardize_ds2(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["age"] = df[_find_column(df, ["Age", "age"])].astype(float)
    out["sbp"] = df[_find_column(df, ["SystolicBP", "Systolic", "SBP", "Systolic BP"])].astype(float)
    out["dbp"] = df[_find_column(df, ["Diastolic", "DiastolicBP", "DBP", "Diastolic BP"])].astype(float)
    out["blood_sugar"] = df[_find_column(df, ["BS", "BloodSugar", "Blood Sugar"])].astype(float)
    out["body_temp"] = df[_find_column(df, ["BodyTemp", "Body Temperature", "Body Temp"])].astype(float)
    out["heart_rate"] = df[_find_column(df, ["HeartRate", "HR", "Heart Rate"])].astype(float)

    optional_cols = {
        "bmi": ["BMI", "bmi"],
        "prev_complications": ["PreviousComplications", "Previous Complications"],
        "preexisting_diabetes": ["PreexistingDiabetes", "Preexisting Diabetes"],
        "gestational_diabetes": ["GestationalDiabetes", "Gestational Diabetes"],
        "mental_health": ["MentalHealth", "Mental Health"],
    }
    for col_name, aliases in optional_cols.items():
        source = _find_column(df, aliases, required=False)
        out[col_name] = df[source] if source else np.nan

    out["risk_level"] = df[_find_column(df, ["RiskLevel", "Risk", "Label", "Risk Level"])].apply(normalize_label)
    return _convert_temp_to_celsius_if_needed(out)


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["pulse_pressure"] = out["sbp"] - out["dbp"]
    out["map"] = (out["sbp"] + 2 * out["dbp"]) / 3.0
    out["hyperglycemia_flag"] = (out["blood_sugar"] > 7.8).astype(int)
    out["age_band"] = out["age"].apply(lambda x: 2 if x < 20 else (1 if x > 35 else 0))
    out["bp_severity"] = out["sbp"].apply(lambda x: 2 if x >= 160 else (1 if x >= 140 else 0))
    return out


def _standardize_ds3(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        'dName':                    'patient_name',
        'Name':                     'patient_name',
        'Age':                      'age',
        'Gravida':                  'gravida',
        'TiTi Tika':                'tt_vaccine',
        'গর্ভকাল':                  'gestational_age_weeks',
        'ওজন':                      'weight_kg',
        'উচ্চতা':                   'height',
        'রক্ত চাপ':                 'blood_pressure_raw',
        'রক্তস্বল্পতা':             'anemia',
        'জন্ডিস':                   'jaundice',
        'গর্ভস্হ শিশু অবস্থান':    'fetal_position',
        'গর্ভস্হ শিশু নাড়াচাড়া':  'fetal_movement',
        'গর্ভস্হ শিশু হৃৎস্পন্দন': 'fetal_heart_rate',
        'প্রসাব পরিক্ষা এলবুমিন':  'urine_albumin',
        'প্রসাব পরিক্ষা সুগার':     'urine_sugar',
        'VDRL':                     'vdrl',
        'HRsAG':                    'hbsag',
        'ঝুকিপূর্ণ গর্ভ':           'risk_label',
        'RiskLevel':                'risk_label',
    }
    df = df.rename(columns=rename_map)

    out = pd.DataFrame()
    out["age"] = df["age"].replace(to_replace=r"[^\d.]", value="", regex=True).apply(pd.to_numeric, errors='coerce') if "age" in df.columns else np.nan
    
    if "blood_pressure_raw" in df.columns:
        bp_split = df["blood_pressure_raw"].astype(str).str.split("/", expand=True)
        out["sbp"] = bp_split[0].apply(pd.to_numeric, errors='coerce') if bp_split.shape[1] > 0 else np.nan
        out["dbp"] = bp_split[1].apply(pd.to_numeric, errors='coerce') if bp_split.shape[1] > 1 else np.nan
    else:
        out["sbp"] = np.nan
        out["dbp"] = np.nan
        
    out["blood_sugar"] = np.nan # Or parse from urine_sugar if we could map correctly
    out["body_temp"] = np.nan
    out["heart_rate"] = np.nan
    
    if "risk_label" in df.columns:
        out["risk_level"] = df["risk_label"].apply(normalize_label)
    else:
        out["risk_level"] = np.nan
        
    return out


def build_merged_dataset(ds1_csv_path: str, ds2_csv_path: str, ds3_csv_path: str) -> Tuple[pd.DataFrame, Dict[str, Dict[str, object]]]:
    """Load, inspect, harmonize, and merge datasets."""
    ds1_raw = pd.read_csv(ds1_csv_path)
    ds2_raw = pd.read_csv(ds2_csv_path)
    try:
        ds3_raw = pd.read_csv(ds3_csv_path, encoding='utf-8')
    except Exception:
        ds3_raw = pd.read_csv(ds3_csv_path, encoding='utf-8', skiprows=1)

    inspection = {
        "DS1": inspect_dataset(ds1_raw, "DS1"),
        "DS2": inspect_dataset(ds2_raw, "DS2"),
        "DS3": inspect_dataset(ds3_raw, "DS3"),
    }

    ds1 = _standardize_ds1(ds1_raw)
    ds2 = _standardize_ds2(ds2_raw)
    ds3 = _standardize_ds3(ds3_raw)

    merged = pd.concat(
        [ds1[CORE_FEATURES + ["risk_level"]], ds2[CORE_FEATURES + ["risk_level"]], ds3[CORE_FEATURES + ["risk_level"]]],
        ignore_index=True,
    )

    merged = merged.dropna(subset=CORE_FEATURES + ["risk_level"]).reset_index(drop=True)
    merged = add_engineered_features(merged)

    return merged, inspection


def split_scale_and_balance(
    merged: pd.DataFrame,
    models_dir: str = "models",
    random_state: int = 42,
) -> Dict[str, object]:
    """Split data, apply SMOTE on training data, scale features, and persist scaler."""
    Path(models_dir).mkdir(parents=True, exist_ok=True)

    X = merged[MODEL_FEATURES]
    y = merged["risk_level"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=random_state,
        stratify=y,
    )

    before_smote = y_train.value_counts().sort_index().to_dict()

    adasyn = ADASYN(random_state=random_state)
    X_train_sm, y_train_sm = adasyn.fit_resample(X_train, y_train)

    after_smote = pd.Series(y_train_sm).value_counts().sort_index().to_dict()

    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train_sm)
    X_test_scaled = scaler.transform(X_test)
    
    joblib.dump(scaler, Path(models_dir) / "scaler.pkl")

    scaler_params = {
        "feature_names": MODEL_FEATURES,
        "data_min": scaler.data_min_.tolist(),
        "data_max": scaler.data_max_.tolist(),
        "scale": scaler.scale_.tolist(),
        "min": scaler.min_.tolist(),
    }
    with (Path(models_dir) / "scaler_params.json").open("w", encoding="utf-8") as fh:
        json.dump(scaler_params, fh, indent=2)

    return {
        "X_train_scaled": X_train_scaled,
        "X_test_scaled": X_test_scaled,
        "y_train_sm": y_train_sm,
        "y_test": y_test.values,
        "X_test_df": X_test.reset_index(drop=True),
        "class_counts_before_smote": before_smote,
        "class_counts_after_smote": after_smote,
        "feature_cols": MODEL_FEATURES,
    }


def save_inspection(inspection: Dict[str, Dict[str, object]], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(inspection, fh, indent=2)
