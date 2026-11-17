"""Import every model so SQLAlchemy metadata and Alembic see all tables."""
from app.models.role import Role
from app.models.user import User
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.pregnancy_profile import PregnancyProfile
from app.models.assessment import Assessment
from app.models.referral import Referral
from app.models.hospital import Hospital
from app.models.alert import Alert
from app.models.outcome import Outcome

__all__ = ["Role", "User", "Patient", "PatientAssignment", "PregnancyProfile", "Assessment", "Referral", "Hospital", "Alert", "Outcome"]
