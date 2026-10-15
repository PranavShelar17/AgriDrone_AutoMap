import pytest
from typing import Generator
from datetime import timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.tenant import User, UserRole


def get_test_token_for(email: str, default_name: str, default_role: UserRole) -> str:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                password_hash=get_password_hash("TestPassword@2026!"),
                full_name=default_name,
                role=default_role,
                is_active=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        return create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "name": user.full_name,
        })
    finally:
        session.close()


# Patch TestClient.__init__ so legacy test files created in Phases 1-8 get Admin auth by default
_orig_testclient_init = TestClient.__init__


def _patched_testclient_init(self, *args, **kwargs):
    headers = kwargs.get("headers")
    if headers is None:
        try:
            admin_tok = get_test_token_for("admin@agridrone.local", "Platform Administrator", UserRole.ADMIN)
            kwargs["headers"] = {"Authorization": f"Bearer {admin_tok}"}
        except Exception:
            pass
    elif "Authorization" in headers and headers["Authorization"] is None:
        # Explicit unauthenticated client
        del headers["Authorization"]
        kwargs["headers"] = headers
    _orig_testclient_init(self, *args, **kwargs)


TestClient.__init__ = _patched_testclient_init


@pytest.fixture(scope="session")
def db_session():
    """Live database session fixture for integration tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def admin_user(db_session):
    return db_session.query(User).filter(User.email == "admin@agridrone.local").first()


@pytest.fixture(scope="session")
def farmer1_user(db_session):
    return db_session.query(User).filter(User.email == "farmer@greenvalley.local").first()


@pytest.fixture(scope="session")
def farmer2_user(db_session):
    return db_session.query(User).filter(User.email == "farmer2@sunrise.local").first()


@pytest.fixture(scope="session")
def admin_token():
    return get_test_token_for("admin@agridrone.local", "Platform Administrator", UserRole.ADMIN)


@pytest.fixture(scope="session")
def farmer1_token():
    return get_test_token_for("farmer@greenvalley.local", "John Doe (Green Valley)", UserRole.FARMER)


@pytest.fixture(scope="session")
def farmer2_token():
    return get_test_token_for("farmer2@sunrise.local", "Jane Smith (Sunrise Orchards)", UserRole.FARMER)


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture with default admin authorization to preserve Phases 1-8 tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def unauth_client() -> Generator[TestClient, None, None]:
    """TestClient without any authorization headers to verify rejection of unauthenticated requests."""
    with TestClient(app, headers={"Authorization": None}) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def farmer1_client(farmer1_token) -> Generator[TestClient, None, None]:
    """TestClient authenticated as Farmer 1 (Green Valley)."""
    with TestClient(app, headers={"Authorization": f"Bearer {farmer1_token}"}) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def farmer2_client(farmer2_token) -> Generator[TestClient, None, None]:
    """TestClient authenticated as Farmer 2 (Sunrise Orchards)."""
    with TestClient(app, headers={"Authorization": f"Bearer {farmer2_token}"}) as test_client:
        yield test_client
