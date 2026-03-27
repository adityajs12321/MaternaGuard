# MaternaGuard Maternal Risk Model - Model Card

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
- Random Forest: accuracy=0.8155, macro_f1=0.7866, high_risk_recall=0.8658
- Gradient Boosting: accuracy=0.7790, macro_f1=0.7486, high_risk_recall=0.8121
- XGBoost: accuracy=0.8360, macro_f1=0.8009, high_risk_recall=0.9128
- ANN: accuracy=0.6629, macro_f1=0.6275, high_risk_recall=0.7450
- Ensemble (All 4): accuracy=0.9021, macro_f1=0.8722, high_risk_recall=0.9463
