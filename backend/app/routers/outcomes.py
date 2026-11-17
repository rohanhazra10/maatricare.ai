from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.outcome import Outcome
from app.models.referral import Referral
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.user import User
from app.schemas.outcome import OutcomeCreate, OutcomeResponse
from app.security.dependencies import require_roles

router = APIRouter(prefix="/api/outcomes", tags=["Outcomes"])

@router.post("/", response_model=OutcomeResponse, status_code=status.HTTP_201_CREATED)
def record_outcome(payload: OutcomeCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("MEDICAL_OFFICER", "ADMIN"))):
    referral = db.query(Referral).filter(Referral.id == payload.referral_id).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.patient_id != payload.patient_id:
        raise HTTPException(status_code=400, detail="Referral does not belong to the supplied patient")
    if not db.query(Patient).filter(Patient.id == payload.patient_id, Patient.is_active.is_(True)).first():
        raise HTTPException(status_code=404, detail="Active patient not found")
    outcome = Outcome(**payload.model_dump())
    db.add(outcome)
    try:
        db.commit(); db.refresh(outcome)
    except Exception:
        db.rollback(); raise
    return outcome

@router.get("/patient/{patient_id}", response_model=List[OutcomeResponse])
def get_patient_outcomes(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles("ASHA", "ANM", "MEDICAL_OFFICER", "ADMIN"))):
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.is_active.is_(True)).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient not found")
    if current_user.role.name in ("ASHA", "ANM"):
        assigned = db.query(PatientAssignment).filter(PatientAssignment.patient_id == patient_id, PatientAssignment.user_id == current_user.id, PatientAssignment.is_active.is_(True)).first()
        if not assigned: raise HTTPException(status_code=404, detail="Patient not found or you do not have access")
    return db.query(Outcome).filter(Outcome.patient_id == patient_id).order_by(Outcome.recorded_at.desc()).all()
