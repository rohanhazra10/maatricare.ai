from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.assessment import Assessment
from app.models.referral import Referral
from app.models.user import User
from app.security.dependencies import require_roles

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Statistics"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(require_roles("ASHA", "ANM", "MEDICAL_OFFICER", "ADMIN"))):
    patients = db.query(Patient).filter(Patient.is_active.is_(True))
    assessments = db.query(Assessment)
    referrals = db.query(Referral)
    if current_user.role.name in ("ASHA", "ANM"):
        patients = patients.join(PatientAssignment, PatientAssignment.patient_id == Patient.id).filter(PatientAssignment.user_id == current_user.id, PatientAssignment.is_active.is_(True))
        assessments = assessments.join(PatientAssignment, PatientAssignment.patient_id == Assessment.patient_id).filter(PatientAssignment.user_id == current_user.id, PatientAssignment.is_active.is_(True))
        referrals = referrals.filter(Referral.referred_by == current_user.id)
    return {
        "total_patients": patients.distinct().count(),
        "high_risk_cases": assessments.filter(Assessment.risk_category.in_(["HIGH", "CRITICAL", "High", "high"])).count(),
        "pending_referrals": referrals.filter(Referral.status == "PENDING").count(),
        "total_referrals": referrals.count(),
    }
