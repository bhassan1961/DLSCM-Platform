import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

import app.database
import app.main
import app.seed

app.database.engine = test_engine
app.database.SessionLocal = TestSession
app.main.engine = test_engine
app.main.SessionLocal = TestSession
app.seed.engine = test_engine
app.seed.SessionLocal = TestSession

from app.main import app


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestSession()
    try:
        from app.models.user import Organization, User

        if db.query(Organization).count() == 0:
            org = Organization(name="Test Org", org_type="ngo", country="Test")
            db.add(org)
            db.flush()
            user = User(
                name="Test User",
                email="test@test.org",
                role="ops_director",
                organization_id=org.id,
                is_active=True,
            )
            db.add(user)
            db.commit()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def auth_headers(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.org"},
    )
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    from app.auth import create_access_token

    token = create_access_token(
        {"sub": "test@test.org", "role": "ops_director", "org_id": 1}
    )
    return {"Authorization": f"Bearer {token}"}
