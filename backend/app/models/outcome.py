from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.database import Base


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(Integer, primary_key=True, index=True)
    referral_id = Column(Integer, ForeignKey("referrals.id"), nullable=False, unique=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    delivery_outcome = Column(String(100), nullable=False)
    notes = Column(String(500), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)