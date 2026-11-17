from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    address = Column(String(255), nullable=True)
    contact_number = Column(String(20), nullable=True)

    # Geospatial coordinates for proximity search
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Maternal health emergency facilities
    facility_level = Column(String(50), default="PHC")
    has_blood_bank = Column(Boolean, default=False)
    has_nicu = Column(Boolean, default=False)
    has_csection = Column(Boolean, default=False)