# Final Submission Runbook

## Live URLs
1. Frontend (primary): https://maternaguard.vercel.app
2. Frontend (preview): https://maternaguard-hwpqljnhp-doniljaison16-1600s-projects.vercel.app
3. Backend: https://maternaguard-backend.onrender.com
4. Health check: https://maternaguard-backend.onrender.com/health

## Open The Live App
1. Open https://maternaguard.vercel.app.
2. Go to the Log tab and enter vitals.
3. Submit prediction and verify risk output.
4. Check Home and Alerts for updated entries.

## 1. Final Repo Check
1. Ensure this repository is public on GitHub.
2. Confirm README is updated and reflects current implementation.
3. Ensure required files are present:
   - final_evaluation_presentation.tex
   - final_demo_script.txt
   - final_demo_script.tex

## 2. Push to GitHub
1. Open terminal in project root.
2. Run:
   - git init  (only if repo is not initialized yet)
   - git add .
   - git commit -m "Final evaluation submission update"
   - git branch -M main
   - git remote add origin <your-github-repo-url>  (skip if already set)
   - git push -u origin main
3. In GitHub repo settings, set visibility to Public.

## 3. Record 2-Minute Demo Video
1. Keep only demo flow in recording (no long intro and no architecture deep-dive).
2. Follow this order:
   - Open app
   - Enter 6 vitals
   - Submit prediction
   - Show risk class + confidence + top factor
   - Show dashboard trend and alert highlight
   - Show provider/patient history view briefly
3. Keep under 2:00 strictly.
4. Upload video (Drive/YouTube unlisted) and copy share link.

## 4. Deploy Backend (Render)
1. Create new Web Service from this GitHub repo.
2. Use render.yaml if prompted.
3. Set required environment variables:
   - DATABASE_URL (auto from Render Postgres)
   - SECRET_KEY
   - ALGORITHM=HS256
   - ACCESS_TOKEN_EXPIRE_MINUTES=1440
   - MODEL_PATH=ml_new/models/model_rf_v1.pkl
   - SCALER_PATH=ml_new/models/scaler.pkl
   - ALLOWED_ORIGINS=<frontend-domain>
4. Deploy and verify:
   - GET /health returns 200.
   - POST /predict returns Low/Mid/High response.

## 5. Deploy Frontend
1. Deploy app folder to Vercel/Netlify.
2. Set frontend API base URL to Render backend URL.
3. Verify end-to-end predict flow from UI.

## 6. Submit Evaluation Form
1. Paste public GitHub repo link.
2. Paste strict 2-minute demo video link.
3. Recheck all links in incognito mode.
4. Submit before deadline.
