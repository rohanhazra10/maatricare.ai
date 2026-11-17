from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
import app.models  # noqa: F401 - register all model metadata

# Routers
from app.routers.auth import router as auth_router
from app.routers.patients import router as patients_router
from app.routers.pregnancy import router as pregnancy_router
from app.routers.risk import router as risk_router
from app.routers.assessments import router as assessments_router
from app.routers.referrals import router as referrals_router
from app.routers.hospitals import router as hospitals_router
from app.routers.dashboard import router as dashboard_router
from app.routers.alerts import router as alerts_router
from app.routers.outcomes import router as outcomes_router

# Security dependencies
from app.security.dependencies import require_roles
from app.models.user import User


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Maternal Health Risk Monitoring and Early Warning System"
)


# --------------------------------------------------
# Database Table Generation (Handled via Alembic Migrations)
# --------------------------------------------------
# Base.metadata.create_all(bind=engine)  <-- Commented out to prevent startup FK mapping crashes


# --------------------------------------------------
# CORS (lets the ASHA and hospital web apps call this API)
# --------------------------------------------------

allowed_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to MAATRICARE.AI Backend",
        "status": "Running"
    }


# --------------------------------------------------
# Health Check Endpoint
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME
    }


# --------------------------------------------------
# Register API Routers
# --------------------------------------------------

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(pregnancy_router)
app.include_router(risk_router)
app.include_router(assessments_router)
app.include_router(referrals_router)
app.include_router(hospitals_router)
app.include_router(dashboard_router)
app.include_router(alerts_router)
app.include_router(outcomes_router)


# --------------------------------------------------
# Temporary Role-Based Access Control Test Endpoints
# --------------------------------------------------

@app.get("/test/asha")
def test_asha_access(
    current_user: User = Depends(require_roles("ASHA"))
):
    return {
        "message": "ASHA access granted",
        "user": current_user.full_name,
        "role": current_user.role.name
    }


@app.get("/test/medical-officer")
def test_medical_officer_access(
    current_user: User = Depends(require_roles("MEDICAL_OFFICER"))
):
    return {
        "message": "Medical Officer access granted",
        "user": current_user.full_name,
        "role": current_user.role.name
    }