"""Shared pytest fixtures — in-memory SQLite with dependency overrides."""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Force test settings before app modules load cached settings / engine.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-32chars"
os.environ["ENVIRONMENT"] = "test"
os.environ["STRIPE_MOCK_MODE"] = "true"
os.environ["VA_MOCK_MODE"] = "true"
os.environ["REDIS_ENABLED"] = "false"

from app.core.config import get_settings
from app.core.rbac import Role
from app.core.security import hash_password
from app.db import models  # noqa: F401 — register models
from app.db.database import Base, get_db
from app.db.models import Role as RoleModel
from app.db.models import Subscription, User, UserProfile, UserRole
from app.main import app
from app.services import state_comparison_service as scs

get_settings.cache_clear()

TEST_ENGINE = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

API = "/api/v1"
DEFAULT_PASSWORD = "TestPass123!"


@pytest.fixture(scope="session", autouse=True)
def _create_tables() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _ensure_role(db: Session, name: str) -> RoleModel:
    role = db.query(RoleModel).filter(RoleModel.name == name).first()
    if role is None:
        role = RoleModel(name=name, description=f"Test role: {name}")
        db.add(role)
        db.flush()
    return role


def create_user(
    db: Session,
    *,
    email: str,
    password: str = DEFAULT_PASSWORD,
    role: str = Role.VETERAN.value,
    display_name: str | None = None,
) -> User:
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    db.add(
        UserProfile(
            user_id=user.id,
            display_name=display_name or email.split("@")[0],
            preferred_jurisdiction="AL",
        )
    )
    role_row = _ensure_role(db, role)
    db.add(UserRole(user_id=user.id, role_id=role_row.id))
    db.add(Subscription(user_id=user.id, tier="free", status="active"))
    db.flush()
    return user


def auth_headers(client: TestClient, email: str, password: str = DEFAULT_PASSWORD) -> dict[str, str]:
    response = client.post(
        f"{API}/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def veteran_user(db: Session) -> User:
    return create_user(db, email="veteran@example.com", role=Role.VETERAN.value)


@pytest.fixture
def admin_user(db: Session) -> User:
    return create_user(db, email="admin@example.com", role=Role.SUPER_ADMIN.value)


@pytest.fixture
def veteran_headers(client: TestClient, veteran_user: User, db: Session) -> dict[str, str]:
    db.commit()
    return auth_headers(client, veteran_user.email)


@pytest.fixture
def admin_headers(client: TestClient, admin_user: User, db: Session) -> dict[str, str]:
    db.commit()
    return auth_headers(client, admin_user.email)


@pytest.fixture
def seeded_jurisdictions(db: Session) -> list[Any]:
    count = scs.ensure_jurisdictions_seeded(db)
    db.commit()
    return count
