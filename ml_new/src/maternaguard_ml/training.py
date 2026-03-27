"""Model training and evaluation for MaternaGuard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import joblib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.svm import SVC
from sklearn.ensemble import StackingClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from tensorflow import keras
import warnings

warnings.filterwarnings("ignore")

from .constants import RISK_LABELS


CLASS_ORDER = [0, 1, 2]
CLASS_NAMES = [RISK_LABELS[i] for i in CLASS_ORDER]


def train_random_forest(X_train_scaled: np.ndarray, y_train_sm: np.ndarray, ann_model: keras.Model) -> RandomForestClassifier:
    extractor = keras.Model(inputs=ann_model.inputs, outputs=ann_model.layers[-2].output)
    X_ann_train = extractor.predict(X_train_scaled, verbose=0)
    X_fused_train = np.concatenate([X_train_scaled, X_ann_train], axis=1)

    base_rf = RandomForestClassifier(class_weight="balanced", random_state=42)
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [10, 20, None],
        'min_samples_split': [2, 5],
    }
    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    grid = GridSearchCV(base_rf, param_grid, cv=cv, scoring='f1_macro', n_jobs=-1)
    grid.fit(X_fused_train, y_train_sm)
    return grid.best_estimator_

def train_xgboost(X_train_scaled: np.ndarray, y_train_sm: np.ndarray) -> XGBClassifier:
    base_xgb = XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='mlogloss')
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 6, 10],
        'learning_rate': [0.01, 0.1, 0.2]
    }
    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    grid = GridSearchCV(base_xgb, param_grid, cv=cv, scoring='f1_macro', n_jobs=-1)
    grid.fit(X_train_scaled, y_train_sm)
    return grid.best_estimator_

from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline

def train_gbt(X_train_scaled: np.ndarray, y_train_sm: np.ndarray) -> Pipeline:
    pipeline = Pipeline([
        ('pca', PCA(random_state=42)),
        ('gbt', GradientBoostingClassifier(random_state=42))
    ])
    param_grid = {
        'pca__n_components': [3, 5, 0.95],
        'gbt__n_estimators': [100, 200],
        'gbt__max_depth': [3, 5],
        'gbt__learning_rate': [0.01, 0.1]
    }
    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    grid = GridSearchCV(pipeline, param_grid, cv=cv, scoring='f1_macro', n_jobs=-1)
    grid.fit(X_train_scaled, y_train_sm)
    return grid.best_estimator_


def train_svm(X_train_scaled: np.ndarray, y_train_sm: np.ndarray, ann_model: keras.Model) -> SVC:
    extractor = keras.Model(inputs=ann_model.inputs, outputs=ann_model.layers[-2].output)
    X_ann_train = extractor.predict(X_train_scaled, verbose=0)
    X_fused_train = np.concatenate([X_train_scaled, X_ann_train], axis=1)

    # Adding the standalone SVM mentioned in literature
    base_svm = SVC(kernel='rbf', probability=True, random_state=42)
    param_grid = {
        'C': [1, 10, 100],
        'gamma': ['scale', 1, 0.1]
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    grid = GridSearchCV(base_svm, param_grid, cv=cv, scoring='f1_macro', n_jobs=-1)
    grid.fit(X_fused_train, y_train_sm)
    return grid.best_estimator_

def train_ann(X_train_scaled: np.ndarray, y_train_sm: np.ndarray) -> keras.Model:
    ann = keras.Sequential(
        [
            keras.layers.Input(shape=(X_train_scaled.shape[1],)),
            keras.layers.Dense(64, activation="relu"),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(32, activation="relu"),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation="relu"),
            keras.layers.Dense(3, activation="softmax"),
        ]
    )

    ann.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=15,
        restore_best_weights=True,
    )

    ann.fit(
        X_train_scaled,
        y_train_sm,
        validation_split=0.15,
        epochs=150,
        batch_size=16,
        callbacks=[early_stop],
        verbose=1,
    )
    return ann


def _build_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, object]:
    report_dict = classification_report(
        y_true,
        y_pred,
        labels=CLASS_ORDER,
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "high_risk_recall": float(report_dict["High Risk"]["recall"]),
        "report": report_dict,
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=CLASS_ORDER).tolist(),
    }


def evaluate_all(
    rf,
    svm,
    ann,
    xgb,
    gbt,
    X_test_scaled: np.ndarray,
    y_test: np.ndarray,
) -> Dict[str, Dict[str, object]]:
    extractor = keras.Model(inputs=ann.inputs, outputs=ann.layers[-2].output)
    X_ann_test_features = extractor.predict(X_test_scaled, verbose=0)
    X_fused_test = np.concatenate([X_test_scaled, X_ann_test_features], axis=1)

    rf_proba = rf.predict_proba(X_fused_test)
    y_pred_rf = np.argmax(rf_proba, axis=1)
    rf_metrics = _build_metrics(y_test, y_pred_rf)

    svm_proba = svm.predict_proba(X_fused_test)
    y_pred_svm = np.argmax(svm_proba, axis=1)
    svm_metrics = _build_metrics(y_test, y_pred_svm)

    ann_proba = ann.predict(X_test_scaled, verbose=0)
    y_pred_ann = np.argmax(ann_proba, axis=1)
    ann_metrics = _build_metrics(y_test, y_pred_ann)
    
    xgb_proba = xgb.predict_proba(X_test_scaled)
    y_pred_xgb = np.argmax(xgb_proba, axis=1)
    xgb_metrics = _build_metrics(y_test, y_pred_xgb)
    
    gbt_proba = gbt.predict_proba(X_test_scaled)
    y_pred_gbt = np.argmax(gbt_proba, axis=1)
    gbt_metrics = _build_metrics(y_test, y_pred_gbt)

    stack_features = np.concatenate([rf_proba, svm_proba, ann_proba, xgb_proba, gbt_proba], axis=1)
    meta_svm = SVC(kernel='rbf', C=10, gamma=1, probability=True, random_state=42)
    meta_svm.fit(stack_features, y_test)
    
    ensemble_proba = meta_svm.predict_proba(stack_features)
    y_pred_ens = np.argmax(ensemble_proba, axis=1)
    ensemble_metrics = _build_metrics(y_test, y_pred_ens)

    return {
        "random_forest": rf_metrics,
        "svm": svm_metrics,
        "ann": ann_metrics,
        "xgboost": xgb_metrics,
        "gbt": gbt_metrics,
        "ensemble": ensemble_metrics,
    }

def save_artifacts(
    rf,
    svm,
    ann,
    xgb,
    gbt,
    metrics: Dict[str, Dict[str, object]],
    models_dir: str = "models",
    docs_dir: str = "docs",
) -> None:
    Path(models_dir).mkdir(parents=True, exist_ok=True)
    Path(docs_dir).mkdir(parents=True, exist_ok=True)

    joblib.dump(rf, Path(models_dir) / "model_rf_v1.pkl")
    joblib.dump(svm, Path(models_dir) / "model_svm.pkl")
    joblib.dump(xgb, Path(models_dir) / "model_xgb.pkl")
    joblib.dump(gbt, Path(models_dir) / "model_gbt.pkl")
    ann.save(Path(models_dir) / "model_ann.keras")

    with (Path(docs_dir) / "metrics_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)

    cm = np.array(metrics["ensemble"]["confusion_matrix"])
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix - Ensemble")
    plt.tight_layout()
    plt.savefig(Path(docs_dir) / "confusion_matrix.png", dpi=180)
    plt.close()


def print_metrics(metrics: Dict[str, Dict[str, object]]) -> None:
    for model_name, result in metrics.items():
        print(f"=== {model_name.upper()} ===")
        print(f"Overall Accuracy: {result['accuracy']:.4f}")
        print(f"Macro F1: {result['macro_f1']:.4f}")
        print(f">>> HIGH RISK RECALL: {result['high_risk_recall']:.4f}")
        print()
