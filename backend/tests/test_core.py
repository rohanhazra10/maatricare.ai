from sqlalchemy.orm import configure_mappers

from app.database import Base, engine
import app.models
from app.models.outcome import Outcome
from app.services.geo import haversine_distance
from app.schemas.outcome import OutcomeCreate


def test_all_models_register_on_one_metadata():
    expected = {
        "roles", "users", "patients", "patient_assignments",
        "pregnancy_profiles", "assessments", "referrals",
        "hospitals", "alerts", "outcomes",
    }
    assert expected.issubset(set(Base.metadata.tables))


def test_sqlalchemy_relationship_mappings_configure():
    configure_mappers()


def test_outcome_referral_foreign_key_exists():
    foreign_keys = {fk.target_fullname for fk in Outcome.__table__.c.referral_id.foreign_keys}
    assert "referrals.id" in foreign_keys


def test_create_all_schema_on_configured_database():
    Base.metadata.create_all(bind=engine)
    assert set(Base.metadata.tables).issubset(set(__import__("sqlalchemy").inspect(engine).get_table_names()))


def test_haversine_distance_zero_for_same_point():
    assert haversine_distance(22.57, 88.36, 22.57, 88.36) == 0


def test_haversine_distance_known_city_pair_is_reasonable():
    distance = haversine_distance(22.5726, 88.3639, 22.5958, 88.2636)
    assert 10 < distance < 12


def test_outcome_schema_rejects_invalid_ids():
    try:
        OutcomeCreate(referral_id=0, patient_id=1, delivery_outcome="Live birth")
    except Exception:
        return
    raise AssertionError("Expected referral_id=0 to be rejected")
