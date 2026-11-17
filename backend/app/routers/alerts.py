from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.security.dependencies import require_roles

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

class AlertResponse(BaseModel):
    id: int
    patient_id: int
    risk_level: str
    message: str
    is_resolved: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=List[AlertResponse])
def list_alerts(db: Session = Depends(get_db), current_user: User = Depends(require_roles("ASHA", "ANM", "MEDICAL_OFFICER", "ADMIN"))):
    query = db.query(Alert)
    if current_user.role.name in ("ASHA", "ANM"):
        from app.models.patient_assignment import PatientAssignment
        query = query.join(PatientAssignment, PatientAssignment.patient_id == Alert.patient_id).filter(PatientAssignment.user_id == current_user.id, PatientAssignment.is_active.is_(True))
    return query.order_by(Alert.created_at.desc()).all()

@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles("MEDICAL_OFFICER", "ADMIN"))):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    try:
        db.commit(); db.refresh(alert)
    except Exception:
        db.rollback(); raise
    return alert
