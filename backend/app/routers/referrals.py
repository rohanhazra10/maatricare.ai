from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.models.referral import Referral
from app.models.user import User
from app.routers.patients import get_assigned_patient
from app.schemas.referral import (
    ReferralCreate,
    ReferralClose,
    ReferralSummary,
    ReferralDetail
)
from app.security.dependencies import require_roles


router = APIRouter(
    prefix="/referrals",
    tags=["Referrals"]
)

FIELD_ROLES = ("ASHA", "ANM")
ALL_ROLES = ("ASHA", "ANM", "MEDICAL_OFFICER", "ADMIN")
VALID_STATUSES = ("PENDING", "ACKNOWLEDGED", "CLOSED")


def to_summary(r: Referral) -> dict:
    return {
        "id": r.id,
        "status": r.status,
        "patient_id": r.patient_id,
        "patient_name": r.patient.full_name,
        "village": r.patient.village,
        "assessment_id": r.assessment_id,
        "risk_category": r.assessment.risk_category,
        "referred_by_name": r.referrer.full_name,
        "created_at": r.created_at,
    }


def get_referral_for_user(referral_id: int, user: User, db: Session) -> Referral:
    referral = db.query(Referral).filter(Referral.id == referral_id).first()

    if not referral:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Referral not found")

    # Field workers only see their own referrals
    if user.role.name not in ("MEDICAL_OFFICER", "ADMIN") and referral.referred_by != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Referral not found")

    return referral


# MANUAL REFERRAL (ASHA / ANM), e.g. for a Mid-risk case
@router.post(
    "/",
    response_model=ReferralSummary,
    status_code=status.HTTP_201_CREATED
)
def create_referral(
    data: ReferralCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*FIELD_ROLES))
):
    assessment = (
        db.query(Assessment)
        .filter(Assessment.id == data.assessment_id)
        .first()
    )

    if not assessment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assessment not found")

    # Must be one of this worker's own patients
    get_assigned_patient(assessment.patient_id, current_user, db)

    existing = (
        db.query(Referral)
        .filter(Referral.assessment_id == assessment.id)
        .first()
    )

    if existing:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "A referral already exists for this assessment"
        )

    referral = Referral(
        assessment_id=assessment.id,
        patient_id=assessment.patient_id,
        referred_by=current_user.id,
        status="PENDING",
        reason=data.reason or "Manual referral by health worker"
    )

    db.add(referral)
    db.commit()
    db.refresh(referral)

    return to_summary(referral)


# LIST REFERRALS
# Medical officers see all; field workers see only their own
@router.get("/", response_model=list[ReferralSummary])
def list_referrals(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES))
):
    query = db.query(Referral)

    if current_user.role.name != "MEDICAL_OFFICER":
        query = query.filter(Referral.referred_by == current_user.id)

    if status_filter:
        wanted = status_filter.strip().upper()
        if wanted not in VALID_STATUSES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "status_filter must be PENDING, ACKNOWLEDGED or CLOSED"
            )
        query = query.filter(Referral.status == wanted)

    referrals = query.order_by(Referral.created_at.desc(), Referral.id.desc()).all()

    return [to_summary(r) for r in referrals]


# REFERRAL DETAIL (with the patient and full assessment history)
@router.get("/{referral_id}", response_model=ReferralDetail)
def get_referral(
    referral_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES))
):
    referral = get_referral_for_user(referral_id, current_user, db)

    history = (
        db.query(Assessment)
        .filter(Assessment.patient_id == referral.patient_id)
        .order_by(Assessment.created_at.desc(), Assessment.id.desc())
        .all()
    )

    detail = to_summary(referral)
    detail.update({
        "reason": referral.reason,
        "officer_notes": referral.officer_notes,
        "assigned_to_name": referral.officer.full_name if referral.officer else None,
        "acknowledged_at": referral.acknowledged_at,
        "closed_at": referral.closed_at,
        "patient": referral.patient,
        "assessments": history,
    })

    return detail


# ACKNOWLEDGE (Medical Officer)
@router.patch("/{referral_id}/acknowledge", response_model=ReferralSummary)
def acknowledge_referral(
    referral_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("MEDICAL_OFFICER"))
):
    referral = get_referral_for_user(referral_id, current_user, db)

    if referral.status != "PENDING":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Only PENDING referrals can be acknowledged (current: {referral.status})"
        )

    referral.status = "ACKNOWLEDGED"
    referral.assigned_to = current_user.id
    referral.acknowledged_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(referral)

    return to_summary(referral)


# CLOSE (Medical Officer)
@router.patch("/{referral_id}/close", response_model=ReferralSummary)
def close_referral(
    referral_id: int,
    data: ReferralClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("MEDICAL_OFFICER"))
):
    referral = get_referral_for_user(referral_id, current_user, db)

    if referral.status != "ACKNOWLEDGED":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Acknowledge the referral before closing it"
        )

    referral.status = "CLOSED"
    referral.officer_notes = data.officer_notes
    referral.closed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(referral)

    return to_summary(referral)
