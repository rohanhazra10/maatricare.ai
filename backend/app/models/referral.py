from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)

    # One referral per assessment
    assessment_id = Column(
        Integer,
        ForeignKey("assessments.id"),
        nullable=False,
        unique=True
    )

    patient_id = Column(
        Integer,
        ForeignKey("patients.id"),
        nullable=False,
        index=True
    )

    # Health worker who referred the case
    referred_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Medical officer who acknowledged it
    assigned_to = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    # PENDING -> ACKNOWLEDGED -> CLOSED
    status = Column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True
    )

    reason = Column(Text, nullable=True)
    officer_notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    assessment = relationship("Assessment")
    patient = relationship("Patient")
    referrer = relationship("User", foreign_keys=[referred_by])
    officer = relationship("User", foreign_keys=[assigned_to])
