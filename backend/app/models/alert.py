from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, false
from datetime import datetime
from sqlalchemy.sql import func
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    risk_level = Column(String(50), nullable=False)
    message = Column(String(255), nullable=False)
    is_resolved = Column(Boolean, default=False, server_default=false(), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)