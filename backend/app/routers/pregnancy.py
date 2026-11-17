from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.pregnancy_profile import PregnancyProfile
from app.models.referral import Referral
from app.models.user import User
from app.routers.patients import get_assigned_patient
from app.schemas.pregnancy import (
    PregnancyCreate,
    PregnancyUpdate,
    PregnancyResponse
)
from app.security.dependencies import require_roles


router = APIRouter(
    prefix="/pregnancies",
    tags=["Pregnancy Management"]
)

FIELD_ROLES = ("ASHA", "ANM")
ALL_ROLES = ("ASHA", "ANM", "MEDICAL_OFFICER", "ADMIN")

PREGNANCY_DAYS = 280


def calculate_edd(lmp: date) -> date:
    """Expected delivery date = LMP + 280 days."""
    return lmp + timedelta(days=PREGNANCY_DAYS)


def to_response(p: PregnancyProfile) -> dict:
    weeks = None
    if p.pregnancy_status == "ONGOING":
        weeks = max(0, (date.today() - p.lmp).days // 7)

    return {
        "id": p.id,
        "patient_id": p.patient_id,
        "pregnancy_number": p.pregnancy_number,
        "lmp": p.lmp,
        "edd": p.edd,
        "gravida": p.gravida,
        "para": p.para,
        "previous_pregnancy_complications": p.previous_pregnancy_complications,
        "registration_date": p.registration_date,
        "pregnancy_status": p.pregnancy_status,
        "created_by": p.created_by,
        "gestational_age_weeks": weeks,
    }


def check_pregnancy_rules(lmp, gravida, para, registration_date, pregnancy_status):
    """Shared validation for create and update."""
    if registration_date < lmp:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Registration date cannot be earlier than LMP"
        )

    # In an ongoing pregnancy, earlier births must be fewer than total pregnancies
    if pregnancy_status == "ONGOING" and para >= gravida:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "For an ongoing pregnancy, para must be less than gravida"
        )

    if para > gravida:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Para cannot be greater than gravida"
        )


def get_pregnancy_for_user(pregnancy_id: int, user: User, db: Session) -> PregnancyProfile:
    """Field workers: only their own patients.
    Medical officers: only patients that have been referred."""
    pregnancy = (
        db.query(PregnancyProfile)
        .filter(PregnancyProfile.id == pregnancy_id)
        .first()
    )

    if not pregnancy:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pregnancy record not found")

    check_patient_access(pregnancy.patient_id, user, db)

    return pregnancy


def check_patient_access(patient_id: int, user: User, db: Session):
    if user.role.name == "MEDICAL_OFFICER":
        referred = (
            db.query(Referral)
            .filter(Referral.patient_id == patient_id)
            .first()
        )
        if not referred:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Patient not found or you do not have access"
            )
        return

    get_assigned_patient(patient_id, user, db)


# CREATE PREGNANCY RECORD
@router.post(
    "/",
    response_model=PregnancyResponse,
    status_code=status.HTTP_201_CREATED
)
def create_pregnancy(
    data: PregnancyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*FIELD_ROLES))
):
    patient = get_assigned_patient(data.patient_id, current_user, db)

    check_pregnancy_rules(
        data.lmp, data.gravida, data.para,
        data.registration_date, "ONGOING"
    )

    existing = (
        db.query(PregnancyProfile)
        .filter(
            PregnancyProfile.patient_id == patient.id,
            PregnancyProfile.pregnancy_status == "ONGOING"
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "This patient already has an ongoing pregnancy. "
            "Mark it DELIVERED or CLOSED first."
        )

    last = (
        db.query(PregnancyProfile)
        .filter(PregnancyProfile.patient_id == patient.id)
        .order_by(PregnancyProfile.pregnancy_number.desc())
        .first()
    )
    next_number = (last.pregnancy_number + 1) if last else 1

    pregnancy = PregnancyProfile(
        patient_id=patient.id,
        pregnancy_number=next_number,
        lmp=data.lmp,
        edd=calculate_edd(data.lmp),
        gravida=data.gravida,
        para=data.para,
        previous_pregnancy_complications=data.previous_pregnancy_complications,
        registration_date=data.registration_date,
        pregnancy_status="ONGOING",
        created_by=current_user.id
    )

    db.add(pregnancy)
    db.commit()
    db.refresh(pregnancy)

    return to_response(pregnancy)


# ALL PREGNANCIES OF ONE PATIENT (newest first)
@router.get(
    "/patient/{patient_id}",
    response_model=list[PregnancyResponse]
)
def list_patient_pregnancies(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES))
):
    check_patient_access(patient_id, current_user, db)

    pregnancies = (
        db.query(PregnancyProfile)
        .filter(PregnancyProfile.patient_id == patient_id)
        .order_by(PregnancyProfile.pregnancy_number.desc())
        .all()
    )

    return [to_response(p) for p in pregnancies]


# ONE PREGNANCY
@router.get("/{pregnancy_id}", response_model=PregnancyResponse)
def get_pregnancy(
    pregnancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES))
):
    return to_response(get_pregnancy_for_user(pregnancy_id, current_user, db))


# UPDATE (partial: send only the fields that changed)
@router.patch("/{pregnancy_id}", response_model=PregnancyResponse)
def update_pregnancy(
    pregnancy_id: int,
    data: PregnancyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*FIELD_ROLES))
):
    pregnancy = get_pregnancy_for_user(pregnancy_id, current_user, db)

    changes = data.model_dump(exclude_unset=True)

    # Drop explicit nulls for fields that cannot be empty
    for field in ("lmp", "gravida", "para", "registration_date", "pregnancy_status"):
        if field in changes and changes[field] is None:
            del changes[field]

    new_lmp = changes.get("lmp", pregnancy.lmp)
    new_gravida = changes.get("gravida", pregnancy.gravida)
    new_para = changes.get("para", pregnancy.para)
    new_reg = changes.get("registration_date", pregnancy.registration_date)
    new_status = changes.get("pregnancy_status", pregnancy.pregnancy_status)

    check_pregnancy_rules(new_lmp, new_gravida, new_para, new_reg, new_status)

    # Re-opening a pregnancy must not create two ongoing ones
    if new_status == "ONGOING" and pregnancy.pregnancy_status != "ONGOING":
        other = (
            db.query(PregnancyProfile)
            .filter(
                PregnancyProfile.patient_id == pregnancy.patient_id,
                PregnancyProfile.pregnancy_status == "ONGOING",
                PregnancyProfile.id != pregnancy.id
            )
            .first()
        )
        if other:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "This patient already has another ongoing pregnancy"
            )

    for field, value in changes.items():
        setattr(pregnancy, field, value)

    # Keep EDD in step with LMP
    pregnancy.edd = calculate_edd(pregnancy.lmp)

    db.commit()
    db.refresh(pregnancy)

    return to_response(pregnancy)
