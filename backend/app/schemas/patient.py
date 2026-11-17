from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class PatientCreate(BaseModel):

    full_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=15)

    address: Optional[str] = None
    village: Optional[str] = Field(None, max_length=100)
    block: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)

    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=15)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Patient name cannot be empty")

        return value


class PatientResponse(BaseModel):

    id: int
    patient_code: str

    full_name: str
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None

    address: Optional[str] = None
    village: Optional[str] = None
    block: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    created_by: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)