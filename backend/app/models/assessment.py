from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(
        Integer,
        ForeignKey("patients.id"),
        nullable=False,
        index=True
    )

    # Optional link to a pregnancy record (used in a later stage)
    pregnancy_id = Column(
        Integer,
        ForeignKey("pregnancy_profiles.id"),
        nullable=True
    )

    # Measurements entered by the health worker
    age = Column(Float, nullable=False)
    sbp = Column(Float, nullable=False)
    dbp = Column(Float, nullable=False)
    temp_f = Column(Float, nullable=False)
    hr = Column(Float, nullable=False)
    bmi = Column(Float, nullable=False)

    # Model output
    risk_category = Column(String(10), nullable=False)
    prob_high = Column(Float, nullable=False)
    prob_low = Column(Float, nullable=False)
    prob_mid = Column(Float, nullable=False)

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    patient = relationship("Patient")
    creator = relationship("User", foreign_keys=[created_by])
