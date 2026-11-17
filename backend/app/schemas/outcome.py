from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class OutcomeCreate(BaseModel):
    referral_id: int = Field(..., gt=0)
    patient_id: int = Field(..., gt=0)
    delivery_outcome: str = Field(..., min_length=2, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)

class OutcomeResponse(BaseModel):
    id: int
    referral_id: int
    patient_id: int
    delivery_outcome: str
    notes: Optional[str] = None
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)
