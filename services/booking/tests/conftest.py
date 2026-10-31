"""
Shared pytest fixtures for the booking service API tests.

Tests run against an in-memory SQLite database and the FastAPI app without
its lifespan, so no Postgres or RabbitMQ is needed. Access tokens are signed
with the service's own JWT settings, so the real authorization code runs.
"""

import json
from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from booking.api.dependencies import get_session
from booking.core.config import settings
from booking.database.models.address import Address
from booking.database.models.organization import Organization
from booking.database.models.organization_type import OrganizationType
from booking.database.models.organization_user_mapping import OrganizationUserMapping
from booking.database.models.users import UsersReplica
from booking.main import app
from booking.types.constants import ACTIVE_ORGANIZATION_HEADER
from booking.types.enums import TokenType, UserType

API_PREFIX = settings.API_V1_STR


@dataclass
class TestUser:
    """A persisted user replica plus the request headers that authenticate it."""

    __test__ = False  # Not a test class, despite the name.

    replica: UsersReplica
    headers: dict[str, str]

    def headers_with_active_organization(self, organization: Organization) -> dict[str, str]:
        """Return the auth headers plus the active organization header."""
        return {**self.headers, ACTIVE_ORGANIZATION_HEADER: str(organization.guid)}


@pytest.fixture
def session() -> Generator[Session]:
    """Yield a session bound to a fresh in-memory SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as test_session:
        yield test_session


@pytest.fixture
def client(session: Session) -> Generator[TestClient]:
    """Yield a test client whose requests use the test database session."""
    app.dependency_overrides[get_session] = lambda: session
    # No `with` block: the lifespan (RabbitMQ connections) is not started.
    yield TestClient(app)
    app.dependency_overrides.clear()


def build_access_token(user: UsersReplica) -> str:
    """Sign an access token for `user` the way the auth service does."""
    # Same claim layout as the auth service issues.
    subject = {"user_guid": str(user.guid), "role": int(user.role), "email_verified": True}
    return jwt.encode(
        {
            "sub": json.dumps(subject),
            "type": int(TokenType.ACCESS),
            "exp": datetime.now(UTC) + timedelta(minutes=15),
        },
        key=settings.JWT_ENCRYPTION_SECRET_KEY,
        algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
    )


@pytest.fixture
def create_user(session: Session) -> Callable[[UserType], TestUser]:
    """Return a factory that persists a user replica with the given role."""
    created_user_count = 0

    def _create_user(role: UserType) -> TestUser:
        nonlocal created_user_count
        created_user_count += 1
        replica = UsersReplica(
            user_id=created_user_count,
            email=f"user{created_user_count}@example.org",
            username=f"user{created_user_count}",
            role=role,
        )
        session.add(replica)
        session.commit()
        session.refresh(replica)
        return TestUser(replica=replica, headers={"Authorization": f"Bearer {build_access_token(replica)}"})

    return _create_user


@pytest.fixture
def admin_user(create_user: Callable[[UserType], TestUser]) -> TestUser:
    return create_user(UserType.ADMIN)


@pytest.fixture
def owner_user(create_user: Callable[[UserType], TestUser]) -> TestUser:
    return create_user(UserType.OWNER)


@pytest.fixture
def manager_user(create_user: Callable[[UserType], TestUser]) -> TestUser:
    return create_user(UserType.MANAGER)


@pytest.fixture
def customer_user(create_user: Callable[[UserType], TestUser]) -> TestUser:
    return create_user(UserType.CUSTOMER)


@pytest.fixture
def create_organization(session: Session) -> Callable[..., Organization]:
    """Return a factory that persists an active organization and maps the given members to it."""

    def _create_organization(name: str, members: list[TestUser]) -> Organization:
        organization_type = OrganizationType(name=f"Type for {name}")
        address = Address(address_line_1="1 Main Road", city="Pune", state="MH", country="India", postal_code=411001)
        session.add_all([organization_type, address])
        session.commit()
        organization = Organization(name=name, organization_type_id=organization_type.id, address_id=address.id)
        session.add(organization)
        session.commit()
        session.refresh(organization)
        for member in members:
            session.add(OrganizationUserMapping(organization_id=organization.id, user_id=member.replica.id))
        session.commit()
        return organization

    return _create_organization
