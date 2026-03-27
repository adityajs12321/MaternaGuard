"""Report generation for accuracy report and model card."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from .constants import MODEL_FEATURES


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def write_accuracy_report(
    metrics: Dict[str, Dict[str, float]],
    inspection: Dict[str, Dict[str, object]],
    class_counts_before_smote: Dict[int, int],
    class_counts_after_smote: Dict[int, int],
    docs_dir: str = "docs",
) -> None:
    Path(docs_dir).mkdir(parents=True, exist_ok=True)

    content = f"""# MaternaGuard Accuracy Report

## 1. Dataset summary
- DS1 + DS2 + DS3 inspection saved in docs/dataset_inspection.json
- DS1 shape: {inspection['DS1']['shape']}
- DS2 shape: {inspection['DS2']['shape']}
- DS3 shape: {inspection['DS3']['shape']}
- Class distribution before SMOTE (train split): {class_counts_before_smote}
- Class distribution after SMOTE (train split): {class_counts_after_smote}

## 2. Feature list (11 total)
{chr(10).join([f"- {f}" for f in MODEL_FEATURES])}

## 3. Results table
| Model | Accuracy | Macro F1 | High Risk Recall |
|---|---:|---:|---:|
| Random Forest | {metrics['random_forest']['accuracy']:.4f} | {metrics['random_forest']['macro_f1']:.4f} | {metrics['random_forest']['high_risk_recall']:.4f} |
| Gradient Boosting | {metrics['gbt']['accuracy']:.4f} | {metrics['gbt']['macro_f1']:.4f} | {metrics['gbt']['high_risk_recall']:.4f} |
| XGBoost | {metrics['xgboost']['accuracy']:.4f} | {metrics['xgboost']['macro_f1']:.4f} | {metrics['xgboost']['high_risk_recall']:.4f} |
| ANN | {metrics['ann']['accuracy']:.4f} | {metrics['ann']['macro_f1']:.4f} | {metrics['ann']['high_risk_recall']:.4f} |
| Ensemble (All 4) | {metrics['ensemble']['accuracy']:.4f} | {metrics['ensemble']['macro_f1']:.4f} | {metrics['ensemble']['high_risk_recall']:.4f} |
| Published benchmark (Togunwa 2023) | 0.9500 | 0.9700 | N/A |

## 4. Confusion matrix image
![Confusion Matrix](confusion_matrix.png)

## 5. SHAP importance chart image
![SHAP High Risk Importance](shap_high_risk_importance.png)

## 6. Key finding
High Risk recall of {metrics['ensemble']['high_risk_recall']:.4f} means we correctly flag {_pct(metrics['ensemble']['high_risk_recall'])} of truly dangerous pregnancies, the clinically critical metric.
"""

    (Path(docs_dir) / "accuracy_report.md").write_text(content, encoding="utf-8")


def write_model_card(metrics: Dict[str, Dict[str, float]], docs_dir: str = "docs") -> None:
    Path(docs_dir).mkdir(parents=True, exist_ok=True)

    content = f"""# MaternaGuard Maternal Risk Model - Model Card

## Intended use
Risk triage tool for pregnant women in rural India.
Input: 6 basic vitals.
Output: Low/Mid/High risk classification with explanation.

## Training data
- UCI DS1 (1,014 records)
- Mendeley DS2 (approximately 1,500)
- DS3 Local Dataset
All from IoT/clinical collection in South/Southeast Asia.

## Features required
Age, Systolic BP, Diastolic BP, Blood Sugar (mmol/L), Body Temp (C), Heart Rate (bpm).
All collectible with basic PHC equipment.

## Out-of-scope uses
- Not a diagnostic tool.
- Not a replacement for clinical judgment.
- Not validated for use outside South Asian population context.
- CTG/fetal monitoring not included in MVP (Phase 2 only).

## Known limitations
- Binary label mapping (Non-High -> Low) for DS2 is conservative.
- Dataset size (around 2,500 expected post merge pre-dropna) is suitable for hackathon prototyping but not clinical deployment.

## Performance
- Random Forest: accuracy={metrics['random_forest']['accuracy']:.4f}, macro_f1={metrics['random_forest']['macro_f1']:.4f}, high_risk_recall={metrics['random_forest']['high_risk_recall']:.4f}
- Gradient Boosting: accuracy={metrics['gbt']['accuracy']:.4f}, macro_f1={metrics['gbt']['macro_f1']:.4f}, high_risk_recall={metrics['gbt']['high_risk_recall']:.4f}
- XGBoost: accuracy={metrics['xgboost']['accuracy']:.4f}, macro_f1={metrics['xgboost']['macro_f1']:.4f}, high_risk_recall={metrics['xgboost']['high_risk_recall']:.4f}
- ANN: accuracy={metrics['ann']['accuracy']:.4f}, macro_f1={metrics['ann']['macro_f1']:.4f}, high_risk_recall={metrics['ann']['high_risk_recall']:.4f}
- Ensemble (All 4): accuracy={metrics['ensemble']['accuracy']:.4f}, macro_f1={metrics['ensemble']['macro_f1']:.4f}, high_risk_recall={metrics['ensemble']['high_risk_recall']:.4f}
"""

    (Path(docs_dir) / "model_card.md").write_text(content, encoding="utf-8")
