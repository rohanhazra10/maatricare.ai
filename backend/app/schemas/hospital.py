from pydantic import BaseModel, ConfigDict
from typing import Optional


class HospitalBase(BaseModel):
    name: str
    district: str
    address: Optional[str] = None
    contact_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    facility_level: Optional[str] = "PHC"
    has_blood_bank: Optional[bool] = False
    has_nicu: Optional[bool] = False
    has_csection: Optional[bool] = False


class HospitalCreate(HospitalBase):
    pass


class HospitalResponse(HospitalBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class HospitalFinderResponse(HospitalResponse):
    distance_km: Optional[float] = None