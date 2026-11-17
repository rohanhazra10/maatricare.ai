from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AssessmentCreate(BaseModel):
    patient_id: int = Field(..., gt=0)
    age: float = Field(..., ge=10, le=60)
    sbp: float = Field(..., ge=40, le=300, description="Systolic BP")
    dbp: float = Field(..., ge=20, le=200, description="Diastolic BP")
    temp_f: float = Field(..., ge=80, le=110, description="Temperature in Fahrenheit")
    hr: float = Field(..., ge=25, le=250, description="Heart rate")
    bmi: float = Field(..., ge=10, le=80)


class AssessmentResponse(BaseModel):
    id: int
    patient_id: int
    pregnancy_id: Optional[int] = None
    age: float
    sbp: float
    dbp: float
    temp_f: float
    hr: float
    bmi: float
    risk_category: str
    prob_high: float
    prob_low: float
    prob_mid: float
    created_by: int
    created_at: datetime

    # Filled when a High-risk result automatically creates a referral
    referral_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
