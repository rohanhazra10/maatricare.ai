from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.models.pregnancy_profile import PregnancyProfile
from app.models.referral import Referral
from app.models.alert import Alert
from app.models.user import User
from app.routers.patients import get_assigned_patient
from app.schemas.assessment import AssessmentCreate, AssessmentResponse
from app.security.dependencies import require_roles
from app.services.risk_service import predict_risk, ModelRuntimeError


router = APIRouter(
    prefix="/assessments",
    tags=["Assessments"]
)

ALLOWED_ROLES = ("ASHA", "ANM", "MEDICAL_OFFICER", "ADMIN")


# CREATE ASSESSMENT (predict + save)
@router.post(
    "/",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_assessment(
    data: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALLOWED_ROLES))
):
    # Only allow assessments for patients assigned to this user
    patient = get_assigned_patient(data.patient_id, current_user, db)

    if data.sbp <= data.dbp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SBP must be greater than DBP"
        )

    try:
        result = predict_risk(
            data.age, data.sbp, data.dbp,
            data.temp_f, data.hr, data.bmi
        )
    except ModelRuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    probs = result["probabilities"]

    # Link to the patient's ongoing pregnancy, if there is one
    ongoing = (
        db.query(PregnancyProfile)
        .filter(
            PregnancyProfile.patient_id == patient.id,
            PregnancyProfile.pregnancy_status == "ONGOING"
        )
        .first()
    )

    assessment = Assessment(
        patient_id=patient.id,
        pregnancy_id=ongoing.id if ongoing else None,
        age=data.age,
        sbp=data.sbp,
        dbp=data.dbp,
        temp_f=data.temp_f,
        hr=data.hr,
        bmi=data.bmi,
        risk_category=result["risk_category"],
        prob_high=probs["High"],
        prob_low=probs["Low"],
        prob_mid=probs["Mid"],
        created_by=current_user.id
    )

    db.add(assessment)
    db.flush()

    # A High-risk result automatically creates an urgent referral
    referral = None
    if assessment.risk_category == "High":
        referral = Referral(
            assessment_id=assessment.id,
            patient_id=patient.id,
            referred_by=current_user.id,
            status="PENDING",
            reason="Automatic referral: model predicted High risk"
        )
        db.add(referral)
        db.add(Alert(
            patient_id=patient.id,
            risk_level="High",
            message="Urgent review recommended: maternal risk model returned High risk. This is a research prototype, not a diagnosis."
        ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(assessment)

    # Not stored on the assessment; only returned in the response
    assessment.referral_id = referral.id if referral else None

    return assessment


# HISTORY FOR ONE PATIENT (newest first)
@router.get(
    "/patient/{patient_id}",
    response_model=list[AssessmentResponse]
)
def get_patient_assessments(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALLOWED_ROLES))
):
    patient = get_assigned_patient(patient_id, current_user, db)

    return (
        db.query(Assessment)
        .filter(Assessment.patient_id == patient.id)
        .order_by(Assessment.created_at.desc(), Assessment.id.desc())
        .all()
    )
