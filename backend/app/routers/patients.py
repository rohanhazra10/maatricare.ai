from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientResponse
from app.security.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/patients",
    tags=["Patient Management"]
)


ALLOWED_ROLES = ("ASHA", "ANM", "MEDICAL_OFFICER", "ADMIN")


def get_assigned_patient(
    patient_id: int,
    current_user: User,
    db: Session
):
    patient = (
        db.query(Patient)
        .join(
            PatientAssignment,
            PatientAssignment.patient_id == Patient.id
        )
        .filter(
            Patient.id == patient_id,
            PatientAssignment.user_id == current_user.id,
            PatientAssignment.is_active == True,
            Patient.is_active == True
        )
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or you do not have access"
        )

    return patient


# REGISTER PATIENT
@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED
)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALLOWED_ROLES))
):
    patient = Patient(
        **patient_data.model_dump(),
        created_by=current_user.id
    )

    db.add(patient)
    db.flush()

    assignment = PatientAssignment(
        patient_id=patient.id,
        user_id=current_user.id,
        assigned_by=current_user.id,
        is_active=True
    )

    db.add(assignment)

    db.commit()
    db.refresh(patient)

    return patient


# GET ALL ASSIGNED PATIENTS
@router.get("/", response_model=list[PatientResponse])
def get_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALLOWED_ROLES))
):
    patients = (
        db.query(Patient)
        .join(
            PatientAssignment,
            PatientAssignment.patient_id == Patient.id
        )
        .filter(
            PatientAssignment.user_id == current_user.id,
            PatientAssignment.is_active == True,
            Patient.is_active == True
        )
        .all()
    )

    return patients


# GET PATIENT BY ID
@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALLOWED_ROLES))
):
    return get_assigned_patient(patient_id, current_user, db)


# UPDATE PATIENT
@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALLOWED_ROLES))
):
    patient = get_assigned_patient(patient_id, current_user, db)

    update_data = patient_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    return patient


# DEACTIVATE PATIENT (SOFT DELETE)
@router.delete("/{patient_id}", response_model=PatientResponse)
def deactivate_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALLOWED_ROLES))
):
    patient = get_assigned_patient(patient_id, current_user, db)

    patient.is_active = False

    db.commit()
    db.refresh(patient)

    return patient