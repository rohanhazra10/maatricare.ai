from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class PregnancyProfile(Base):
    __tablename__ = "pregnancy_profiles"

    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "pregnancy_number",
            name="uq_patient_pregnancy_number"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    patient_id = Column(
        Integer,
        ForeignKey("patients.id"),
        nullable=False,
        index=True
    )

    pregnancy_number = Column(
        Integer,
        nullable=False
    )

    lmp = Column(
        Date,
        nullable=False
    )

    edd = Column(
        Date,
        nullable=False
    )

    gravida = Column(
        Integer,
        nullable=False
    )

    para = Column(
        Integer,
        nullable=False
    )

    previous_pregnancy_complications = Column(
        Text,
        nullable=True
    )

    registration_date = Column(
        Date,
        nullable=False
    )

    pregnancy_status = Column(
        String(20),
        nullable=False,
        default="ONGOING"
    )

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

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    patient = relationship("Patient")

    creator = relationship(
        "User",
        foreign_keys=[created_by]
    )