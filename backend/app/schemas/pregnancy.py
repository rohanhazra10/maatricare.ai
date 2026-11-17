from datetime import date
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator


PregnancyStatus = Literal["ONGOING", "DELIVERED", "CLOSED"]


class PregnancyCreate(BaseModel):
    patient_id: int = Field(..., gt=0)

    # Last menstrual period
    lmp: date

    gravida: int = Field(..., ge=1, le=20, description="Total pregnancies including this one")
    para: int = Field(..., ge=0, le=20, description="Previous births")

    previous_pregnancy_complications: Optional[str] = Field(None, max_length=2000)

    registration_date: date = Field(default_factory=date.today)

    @field_validator("lmp")
    @classmethod
    def lmp_not_in_future(cls, value):
        if value > date.today():
            raise ValueError("LMP cannot be a future date")
        return value


class PregnancyUpdate(BaseModel):
    lmp: Optional[date] = None
    gravida: Optional[int] = Field(None, ge=1, le=20)
    para: Optional[int] = Field(None, ge=0, le=20)
    previous_pregnancy_complications: Optional[str] = Field(None, max_length=2000)
    registration_date: Optional[date] = None
    pregnancy_status: Optional[PregnancyStatus] = None

    @field_validator("lmp")
    @classmethod
    def lmp_not_in_future(cls, value):
        if value is not None and value > date.today():
            raise ValueError("LMP cannot be a future date")
        return value


class PregnancyResponse(BaseModel):
    id: int
    patient_id: int
    pregnancy_number: int
    lmp: date
    edd: date
    gravida: int
    para: int
    previous_pregnancy_complications: Optional[str] = None
    registration_date: date
    pregnancy_status: str
    created_by: int

    # Calculated when the response is built (only for ONGOING pregnancies)
    gestational_age_weeks: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
