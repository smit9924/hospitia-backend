"""API tests for the admin organization listing (`/organization/list-for-admin`)."""

from collections.abc import Callable

from fastapi.testclient import TestClient

from booking.database.models.organization import Organization
from tests.conftest import API_PREFIX, TestUser


def test_organization_with_a_manager_is_listed_once_with_its_owner(
    client: TestClient,
    admin_user: TestUser,
    owner_user: TestUser,
    manager_user: TestUser,
    create_organization: Callable[..., Organization],
) -> None:
    create_organization("Sunrise Guest House", [owner_user, manager_user])

    response = client.get(f"{API_PREFIX}/organization/list-for-admin", headers=admin_user.headers)

    assert response.status_code == 200
    body = response.json()
    assert body["totalCount"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["ownerDisplayName"] is not None
