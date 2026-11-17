"""Smoke/integration tests. These run after installing requirements.txt."""
import pytest
pytest.importorskip("jose", reason="Install backend requirements to run API integration tests")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
import app.models
from app.models.role import Role
from app.main import app


@pytest.fixture()
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    db.add_all([
        Role(name="ASHA", description="Test ASHA"),
        Role(name="ANM", description="Test ANM"),
        Role(name="MEDICAL_OFFICER", description="Test Medical Officer"),
        Role(name="ADMIN", description="Test administrator"),
    ])
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_dashboard_requires_authentication(client):
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 401


def test_registration_and_login(client):
    registered = client.post("/auth/register", json={
        "full_name": "Test ASHA", "email": "asha@example.com",
        "password": "StrongTestPass123!", "role": "ASHA"
    })
    assert registered.status_code == 201, registered.text
    login = client.post("/auth/login", json={
        "email": "asha@example.com", "password": "StrongTestPass123!"
    })
    assert login.status_code == 200, login.text
    assert login.json()["token_type"] == "bearer"
