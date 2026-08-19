import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.seed import seed_all

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestSession()
    try:
        from app.models.user import Organization, User

        if db.query(Organization).count() == 0:
            seed_all.__wrapped__ if hasattr(seed_all, "__wrapped__") else None
            from app.models.user import Organization as Org

            org = Org(name="Test Org", org_type="ngo", country="Test")
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
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    return TestClient(app, raise_server_exceptions=False)


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
