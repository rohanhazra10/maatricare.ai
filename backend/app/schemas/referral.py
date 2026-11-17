from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.assessment import AssessmentResponse
from app.schemas.patient import PatientResponse


class ReferralCreate(BaseModel):
    assessment_id: int = Field(..., gt=0)
    reason: Optional[str] = Field(None, max_length=1000)


class ReferralClose(BaseModel):
    officer_notes: Optional[str] = Field(None, max_length=2000)


class ReferralSummary(BaseModel):
    id: int
    status: str
    patient_id: int
    patient_name: str
    village: Optional[str] = None
    assessment_id: int
    risk_category: str
    referred_by_name: str
    created_at: datetime


class ReferralDetail(ReferralSummary):
    reason: Optional[str] = None
    officer_notes: Optional[str] = None
    assigned_to_name: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    patient: PatientResponse
    assessments: list[AssessmentResponse]
