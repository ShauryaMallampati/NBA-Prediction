# Next Steps for NBA World Model

## 1. Data Pipeline
- [ ] **Automate Highlights Fetching**: Set up a cron job to run `scripts/fetch_highlights.py` daily.
- [ ] **Real Live Data**: Connect `src/api/live_odds.py` to a paid API plan for more frequent updates.
- [ ] **Historical Data**: Import more historical game data for better Ensemble training.

## 2. Model Improvements
- [ ] **Vision Model**: Train on real game clips (currently using dummy/limited data).
- [ ] **RNN Model**: Add more features like player fatigue, momentum, and crowd noise.
- [ ] **Ensemble**: Add more models (e.g., CatBoost, LightGBM).

## 3. Application Integration
- [ ] **Frontend**: Display live win probability charts in `app/live/page.tsx`.
- [ ] **Alerts**: Send notifications when high-confidence betting opportunities arise.
- [ ] **Dashboard**: Create a admin dashboard to monitor model performance.

## 4. Deployment
- [ ] **Dockerize**: Create a Docker container for the entire application.
- [ ] **Cloud**: Deploy to AWS/GCP/Azure with GPU support for the Vision model.
