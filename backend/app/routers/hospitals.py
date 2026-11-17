from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.hospital import Hospital
from app.models.user import User
from app.schemas.hospital import HospitalCreate, HospitalResponse, HospitalFinderResponse
from app.security.dependencies import get_current_user, require_roles
from app.services.geo import haversine_distance

router = APIRouter(prefix="/api/hospitals", tags=["Hospitals"])

@router.post("/", response_model=HospitalResponse, status_code=201)
def create_hospital(hospital: HospitalCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("MEDICAL_OFFICER", "ADMIN"))):
    record = Hospital(**hospital.model_dump())
    db.add(record)
    try:
        db.commit(); db.refresh(record)
    except Exception:
        db.rollback(); raise
    return record

@router.get("/", response_model=List[HospitalResponse])
def list_hospitals(district: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Hospital)
    if district: query = query.filter(Hospital.district.ilike(f"%{district}%"))
    return query.order_by(Hospital.name.asc()).all()

@router.get("/find/nearby", response_model=List[HospitalFinderResponse])
def find_nearby_hospitals(lat: float = Query(..., ge=-90, le=90), lng: float = Query(..., ge=-180, le=180), radius_km: float = Query(30.0, gt=0, le=500), requires_blood_bank: bool = False, requires_nicu: bool = False, requires_csection: bool = False, facility_level: Optional[str] = None, limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Hospital).filter(Hospital.latitude.isnot(None), Hospital.longitude.isnot(None))
    if requires_blood_bank: query = query.filter(Hospital.has_blood_bank.is_(True))
    if requires_nicu: query = query.filter(Hospital.has_nicu.is_(True))
    if requires_csection: query = query.filter(Hospital.has_csection.is_(True))
    if facility_level: query = query.filter(Hospital.facility_level.ilike(facility_level.strip()))
    results = []
    for hospital in query.all():
        distance = haversine_distance(lat, lng, hospital.latitude, hospital.longitude)
        if distance <= radius_km:
            data = HospitalFinderResponse.model_validate(hospital)
            data.distance_km = distance
            results.append(data)
    return sorted(results, key=lambda item: item.distance_km or 0)[:limit]
