# MAATRICARE.AI — Member 2 Backend

FastAPI backend for patient and pregnancy records, maternal risk assessments, referrals, hospital discovery, alerts and delivery outcomes. This is a software/research prototype and is **not clinically validated**; do not use its predictions as a diagnosis or substitute for qualified clinical judgment.

## Quick start (VS Code / Windows)

1. Install Python 3.10–3.12.
2. Open this `backend` folder in VS Code.
3. Run `start_windows.bat` (first run creates `.venv`, installs dependencies, creates a local SQLite database, seeds roles and starts the API).
4. Open `http://127.0.0.1:8000/docs` for Swagger UI and `http://127.0.0.1:8000/health` for health status.

On macOS/Linux, run `chmod +x start_unix.sh && ./start_unix.sh`.

## Manual setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Windows: copy .env.example .env
python create_tables.py
python seed_roles.py
uvicorn app.main:app --reload
```

The default database is `sqlite:///./maatricare.db`; no MySQL server is required for local evaluation. To use MySQL, set `DATABASE_URL` in `.env` to a valid `mysql+pymysql://...` URL before creating tables. Never commit or share `.env`. Change `SECRET_KEY` to a long random value before deployment.

## Roles and first user

The role seeder creates `ASHA`, `ANM`, `MEDICAL_OFFICER`, and `ADMIN`. Public registration accepts ASHA/ANM only. Medical Officer and Admin accounts must be provisioned by a trusted administrator; do not expose administrator provisioning publicly.

## Main API groups

- `/auth`: registration, login, current profile
- `/patients`, `/pregnancy`: patient and pregnancy records
- `/assessments`, `/risk`: risk assessment and model prediction
- `/referrals`: referral workflow
- `/api/hospitals`: hospital directory and nearby search
- `/api/alerts`: authenticated alert review/resolution
- `/api/outcomes`: medical-officer outcome recording and authorized history
- `/api/dashboard`: role-scoped summary counts

Use `Authorization: Bearer <access_token>` for protected endpoints.

## Database migrations

For a fresh local/demo database, `create_tables.py` creates the current SQLAlchemy metadata. For a managed deployment, use Alembic instead: `alembic upgrade head`. Do not run both initialization methods against a database whose migration history is unknown.

## Tests

Run `pytest -q`. Automated tests should be expanded as integration services and clinical workflows are finalized. The ML model file must remain in `app/ml/optimized_xgboost_pipeline.joblib`; its training provenance and exact runtime compatibility should be verified before production use.

## Security and deployment checklist

- Replace the development secret key and use HTTPS.
- Configure a production database and restrict database credentials.
- Configure `CORS_ORIGINS` to exact trusted frontend origins.
- Use admin-provisioned privileged accounts and strong passwords.
- Back up and protect maternal health data; apply applicable privacy and health-data regulations.
- Run migrations, security review, load tests and clinical validation before any real-world deployment.
