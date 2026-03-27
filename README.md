# MaternaGuard

MaternaGuard is a maternal health risk triage platform for low-resource settings.
It combines a trained ML risk model, a FastAPI backend, and a React web app to help identify high-risk pregnancy cases early and support faster escalation.

## IMPACT AND BENEFITS

**70,000+**  
Maternal deaths in India/year

**67%**  
Preventable with early detection

**< 5s**  
Time to triage result

**800M+**  
Underserved Indians in rural

**SDG-3 Aligned • Good Health & Well-being • Ayushman Bharat Integration Ready • NHM Programme Compatible**

### Social & Health Impact
- **Saves lives** — flags high-risk before crisis, not after
- **Empowers ASHA workers** with clinical AI on basic Android
- **Fills last-mile gap** — no hospital infrastructure needed
- **Auto SMS referral** eliminates manual escalation delay

### Economic & Scalability
- **₹0 Zero-cost stack** — free-tier tools, no licensing fees
- **Scales nationally** via REST API + Ayushman Bharat stack
- **Reduces unnecessary referrals** — saves transport & tertiary costs
- **Open-source** — publishable for global maternal health research
- **Sustainable:** runs on existing phones, no new hardware needed

## What The System Does

Input vitals used in app prediction flow:
1. Age
2. Systolic BP
3. Diastolic BP
4. Blood Sugar
5. Body Temperature
6. Heart Rate

The system predicts one of three classes:
1. Low Risk
2. Mid Risk
3. High Risk

For high-risk predictions, the app records an in-app visual alert mimicking a referral SMS push. 

## ML Pipeline And Models

### Architectural Improvements
- **Data Harmonization**: Integrated DS1 (UCI), DS2 (Mendeley), and DS3 (Mendeley - translated Bengali features) and defensively cleaned ambiguous 'non high' labels.
- **Class Balancing**: Upgraded from SMOTE to **ADASYN**, specifically targeting the Low/Mid risk confusion zone.
- **Cross-Validation & Tuning**: Transitioned to 10-fold/5-fold Stratified K-Fold CV with `GridSearchCV` hyperparameter tuning.
- **MaternalNET-RF Feature Fusion**: Extracted 16-dimensional activations from the ANN's penultimate layer, concatenated with original features, and fed into the Random Forest and SVM models for non-linear representation.
- **Selective PCA**: Optimized Gradient Boosting trees using a PCA dimensional reduction pipeline.
- **Stacking Meta-Learner**: Replaced basic probability averaging with an **SVM (RBF Kernel, C=10, gamma=1)** meta-learner that intelligently combines the output matrices of RF, SVM, ANN, XGB, and GBT.

### Model Performance Results

Based on the merging of unifying DS1, DS2, and DS3 with ADASYN and our Stacking architecture, here are the evaluation results for all models we developed:

**Random Forest (Feature Fused)**
- Overall Accuracy: 0.8155
- Macro F1: 0.7866
- High Risk Recall: 0.8658

**SVM (RBF Kernel)**
- Overall Accuracy: 0.7267
- Macro F1: 0.6986
- High Risk Recall: 0.7718

**ANN**
- Overall Accuracy: 0.6629
- Macro F1: 0.6275
- High Risk Recall: 0.7450

**XGBoost**
- Overall Accuracy: 0.8360
- Macro F1: 0.8009
- High Risk Recall: 0.9128

**Gradient Boosting (PCA piped)**
- Overall Accuracy: 0.7790
- Macro F1: 0.7486
- High Risk Recall: 0.8121

**Ensemble Meta-Learner (SVM Stacking)**
- Overall Accuracy: **0.9021**
- Macro F1: **0.8722**
- High Risk Recall: **0.9463**


### Research and External References
1. **DS1**: Ahmed, M. (2020). UCI ML Repository #863. IoT-collected, rural Bangladesh. 1,014 records, 6 features, 3-class labels (Low/Mid/High Risk). CC BY 4.0.
2. **DS2**: Mojumdar et al. (2024). Mendeley Data, DOI: 10.17632/p5w98dvbbk.1. 12 features incl. BMI, prev. complications, gestational diabetes, mental health. CC BY 4.0.
3. **DS3**: Chayan, A.R. (2024). Mendeley Data, DOI: 10.17632/8k9pvpmykk/1. Obstetric history: gravida, gestational age, fetal heart rate, anemia. IEEE DataPort.

*Dataset composition metrics and evaluation data are preserved in `ml_new/docs/`.*

## Tech Stack

1. **Frontend:** React + Vite
2. **Backend:** FastAPI + SQLAlchemy + JWT auth
3. **Database:** SQLite (local), PostgreSQL (Render deployment)
4. **ML:** Scikit-Learn, TensorFlow, and XGBoost artifacts in `ml_new/models`
5. **Explainability:** SHAP support in backend services

Supporting root files:
1. `requirements.txt`
2. `.env.example`
3. `render.yaml`
4. `docker-compose.yml`
5. `Dockerfile`

## Local Run (Quick)

Backend:
1. Create and activate a Python virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and update variables.
4. Start API with `uvicorn backend.app:app --reload`.

Frontend:
1. Open `app/`.
2. Install Node packages.
3. Start with `npm run dev`.

## Deployment Notes

1. Backend deployment target: Render using `render.yaml`.
2. Database: Render Postgres for hosted environment.
3. Frontend deployment: Vercel/Netlify (set API base URL to backend domain).
4. ML artifacts are loaded from `ml_new/models` at runtime.

## What Is Done Vs Pending

Done:
1. Model integration with backend prediction API.
2. Frontend prediction workflow and dashboard risk display.
3. Demo-level high-risk alert behavior.
4. Multi-model training artifacts and reports in `ml_new/docs`.

Pending for real-world deployment:
1. Formal clinical validation.
2. Government and hospital process integration.
3. Operational referral workflow approvals.
4. Production identity and access management.
5. Hardened offline-first and network-failure handling for field rollout.
