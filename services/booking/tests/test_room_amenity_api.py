"""API tests for room amenity management (`/room-amenity`)."""

from collections.abc import Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from booking.database.models.organization import Organization
from booking.types.enums import UserType
from booking.types.error_codes import ErrorCodes
from tests.conftest import API_PREFIX, TestUser

ROOM_AMENITY_URL = f"{API_PREFIX}/room-amenity"


@pytest.fixture
def organization(create_organization: Callable[..., Organization], owner_user: TestUser, manager_user: TestUser) -> Organization:
    """Active organization of `owner_user` and `manager_user`."""
    return create_organization("Sunrise Guest House", [owner_user, manager_user])


@pytest.fixture
def other_organization(create_organization: Callable[..., Organization], create_user) -> Organization:
    """Active organization the test owner and manager do not belong to."""
    return create_organization("Other Guest House", [create_user(UserType.OWNER)])


def create_amenity(client: TestClient, headers: dict[str, str], **fields) -> dict:
    """Create an amenity through the API and return the response body."""
    response = client.post(f"{ROOM_AMENITY_URL}/create", json={"name": "Television", **fields}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_admin_creates_default_and_custom_amenities(client: TestClient, admin_user: TestUser, organization: Organization) -> None:
    default = create_amenity(client, admin_user.headers, name="  Television  ", description="  ")
    custom = create_amenity(client, admin_user.headers, name="Geyser", organizationGuid=str(organization.guid))

    assert default["name"] == "Television"
    assert default["description"] is None
    assert default["isDefault"] is True
    assert default["organization"] is None
    assert custom["isDefault"] is False
    assert custom["organization"] == {"guid": str(organization.guid), "name": "Sunrise Guest House"}


def test_admin_cannot_create_amenity_for_unknown_organization(client: TestClient, admin_user: TestUser) -> None:
    response = client.post(
        f"{ROOM_AMENITY_URL}/create",
        json={"name": "Geyser", "organizationGuid": str(uuid4())},
        headers=admin_user.headers,
    )

    assert response.status_code == 404
    assert response.json()["errorCode"] == ErrorCodes.ORGANIZATION_NOT_FOUND


def test_member_creates_custom_amenity_of_active_organization(
    client: TestClient,
    manager_user: TestUser,
    organization: Organization,
    other_organization: Organization,
) -> None:
    # organizationGuid is ignored for members: the active organization wins.
    custom = create_amenity(
        client,
        manager_user.headers_with_active_organization(organization),
        name="Fridge",
        organizationGuid=str(other_organization.guid),
    )

    assert custom["isDefault"] is False
    assert custom["organization"]["guid"] == str(organization.guid)


@pytest.mark.usefixtures("organization")
def test_member_requests_require_a_valid_active_organization(
    client: TestClient,
    owner_user: TestUser,
    other_organization: Organization,
) -> None:
    missing_header = client.get(ROOM_AMENITY_URL, headers=owner_user.headers)
    foreign_organization = client.get(ROOM_AMENITY_URL, headers=owner_user.headers_with_active_organization(other_organization))

    assert missing_header.status_code == 400
    assert missing_header.json()["errorCode"] == ErrorCodes.ACTIVE_ORGANIZATION_REQUIRED
    assert foreign_organization.status_code == 403
    assert foreign_organization.json()["errorCode"] == ErrorCodes.ACTIVE_ORGANIZATION_INVALID


def test_customer_cannot_use_room_amenities(client: TestClient, customer_user: TestUser) -> None:
    assert client.get(ROOM_AMENITY_URL, headers=customer_user.headers).status_code == 401


def test_names_are_unique_case_insensitively_per_scope(
    client: TestClient,
    admin_user: TestUser,
    owner_user: TestUser,
    organization: Organization,
    other_organization: Organization,
) -> None:
    owner_headers = owner_user.headers_with_active_organization(organization)
    create_amenity(client, admin_user.headers, name="Television")
    create_amenity(client, owner_headers, name="Fridge")

    duplicate_default = client.post(f"{ROOM_AMENITY_URL}/create", json={"name": "television"}, headers=admin_user.headers)
    custom_repeating_default = client.post(f"{ROOM_AMENITY_URL}/create", json={"name": "TELEVISION"}, headers=owner_headers)
    duplicate_custom = client.post(f"{ROOM_AMENITY_URL}/create", json={"name": "fridge"}, headers=owner_headers)

    assert duplicate_default.status_code == 409
    assert custom_repeating_default.status_code == 409
    assert custom_repeating_default.json()["message"] == "A default room amenity with this name already exists."
    assert duplicate_custom.status_code == 409
    assert duplicate_custom.json()["errorCode"] == ErrorCodes.ROOM_AMENITY_ALREADY_EXISTS

    # The same custom name is fine in another organization, and as a new default.
    create_amenity(client, admin_user.headers, name="Fridge", organizationGuid=str(other_organization.guid))
    create_amenity(client, admin_user.headers, name="Fridge")


def test_invalid_amenity_fields_are_rejected(client: TestClient, admin_user: TestUser) -> None:
    for payload in ({"name": "   "}, {"name": "x" * 101}, {"name": "Fan", "description": "x" * 501}):
        response = client.post(f"{ROOM_AMENITY_URL}/create", json=payload, headers=admin_user.headers)
        assert response.status_code == 422, payload


def test_listing_scopes_by_role(
    client: TestClient,
    admin_user: TestUser,
    owner_user: TestUser,
    organization: Organization,
    other_organization: Organization,
) -> None:
    create_amenity(client, admin_user.headers, name="Television")
    create_amenity(client, owner_user.headers_with_active_organization(organization), name="Fridge")
    create_amenity(client, admin_user.headers, name="Air conditioner", organizationGuid=str(other_organization.guid))

    member_listing = client.get(ROOM_AMENITY_URL, headers=owner_user.headers_with_active_organization(organization)).json()
    admin_listing = client.get(ROOM_AMENITY_URL, headers=admin_user.headers).json()

    assert [item["name"] for item in member_listing["items"]] == ["Fridge", "Television"]
    assert [item["name"] for item in admin_listing["items"]] == ["Air conditioner", "Fridge", "Television"]

    searched = client.get(ROOM_AMENITY_URL, params={"searchTerm": "tele"}, headers=admin_user.headers).json()
    assert searched["totalCount"] == 1
    paged = client.get(ROOM_AMENITY_URL, params={"pageSize": 1, "pageNumber": 2, "sortDirection": "desc"}, headers=admin_user.headers).json()
    assert [item["name"] for item in paged["items"]] == ["Fridge"]


def test_custom_amenities_of_deleted_organizations_are_hidden_from_admin(
    client: TestClient,
    session,
    admin_user: TestUser,
    other_organization: Organization,
) -> None:
    custom = create_amenity(client, admin_user.headers, name="Fridge", organizationGuid=str(other_organization.guid))
    other_organization.is_active = False
    session.add(other_organization)
    session.commit()

    assert client.get(ROOM_AMENITY_URL, headers=admin_user.headers).json()["totalCount"] == 0
    assert client.get(f"{ROOM_AMENITY_URL}/{custom['guid']}", headers=admin_user.headers).status_code == 404


def test_member_cannot_see_or_change_other_organizations_amenities(
    client: TestClient,
    admin_user: TestUser,
    owner_user: TestUser,
    organization: Organization,
    other_organization: Organization,
) -> None:
    foreign = create_amenity(client, admin_user.headers, name="Fridge", organizationGuid=str(other_organization.guid))
    owner_headers = owner_user.headers_with_active_organization(organization)

    get_response = client.get(f"{ROOM_AMENITY_URL}/{foreign['guid']}", headers=owner_headers)
    update_response = client.put(f"{ROOM_AMENITY_URL}/create", json={"guid": foreign["guid"], "name": "Mine"}, headers=owner_headers)
    delete_response = client.delete(f"{ROOM_AMENITY_URL}/delete", params={"guid": foreign["guid"]}, headers=owner_headers)

    for response in (get_response, update_response, delete_response):
        assert response.status_code == 404
        assert response.json()["errorCode"] == ErrorCodes.ROOM_AMENITY_NOT_FOUND


def test_member_can_read_but_not_change_default_amenities(
    client: TestClient,
    admin_user: TestUser,
    manager_user: TestUser,
    organization: Organization,
) -> None:
    default = create_amenity(client, admin_user.headers, name="Television")
    manager_headers = manager_user.headers_with_active_organization(organization)

    assert client.get(f"{ROOM_AMENITY_URL}/{default['guid']}", headers=manager_headers).status_code == 200
    update_response = client.put(f"{ROOM_AMENITY_URL}/create", json={"guid": default["guid"], "name": "TV"}, headers=manager_headers)
    delete_response = client.delete(f"{ROOM_AMENITY_URL}/delete", params={"guid": default["guid"]}, headers=manager_headers)

    for response in (update_response, delete_response):
        assert response.status_code == 403
        assert response.json()["errorCode"] == ErrorCodes.ROOM_AMENITY_MODIFICATION_FORBIDDEN


def test_update_keeps_scope_and_checks_names(
    client: TestClient,
    admin_user: TestUser,
    owner_user: TestUser,
    organization: Organization,
) -> None:
    owner_headers = owner_user.headers_with_active_organization(organization)
    create_amenity(client, admin_user.headers, name="Television")
    fridge = create_amenity(client, owner_headers, name="Fridge")
    create_amenity(client, owner_headers, name="Kettle")

    renamed = client.put(
        f"{ROOM_AMENITY_URL}/create",
        json={"guid": fridge["guid"], "name": "FRIDGE", "description": "Mini fridge"},
        headers=owner_headers,
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "FRIDGE"
    assert renamed.json()["organization"]["guid"] == str(organization.guid)

    taken_by_sibling = client.put(f"{ROOM_AMENITY_URL}/create", json={"guid": fridge["guid"], "name": "kettle"}, headers=owner_headers)
    taken_by_default = client.put(f"{ROOM_AMENITY_URL}/create", json={"guid": fridge["guid"], "name": "Television"}, headers=owner_headers)
    assert taken_by_sibling.status_code == 409
    assert taken_by_default.status_code == 409

    # Admins may edit an organization's custom amenity; the scope stays the same.
    admin_rename = client.put(f"{ROOM_AMENITY_URL}/create", json={"guid": fridge["guid"], "name": "Refrigerator"}, headers=admin_user.headers)
    assert admin_rename.status_code == 200
    assert admin_rename.json()["isDefault"] is False


def test_deleted_amenity_is_gone_and_its_name_can_be_reused(
    client: TestClient,
    owner_user: TestUser,
    organization: Organization,
) -> None:
    owner_headers = owner_user.headers_with_active_organization(organization)
    fridge = create_amenity(client, owner_headers, name="Fridge")

    assert client.delete(f"{ROOM_AMENITY_URL}/delete", params={"guid": fridge["guid"]}, headers=owner_headers).status_code == 204
    assert client.get(f"{ROOM_AMENITY_URL}/{fridge['guid']}", headers=owner_headers).status_code == 404
    assert client.delete(f"{ROOM_AMENITY_URL}/delete", params={"guid": fridge["guid"]}, headers=owner_headers).status_code == 404
    create_amenity(client, owner_headers, name="fridge")


def test_selectable_amenities_combine_defaults_and_organization_custom_ones(
    client: TestClient,
    admin_user: TestUser,
    owner_user: TestUser,
    organization: Organization,
    other_organization: Organization,
) -> None:
    create_amenity(client, admin_user.headers, name="Television")
    create_amenity(client, owner_user.headers_with_active_organization(organization), name="fridge")
    create_amenity(client, admin_user.headers, name="Kettle", organizationGuid=str(other_organization.guid))

    member_options = client.get(f"{ROOM_AMENITY_URL}/selectable", headers=owner_user.headers_with_active_organization(organization)).json()
    admin_defaults_only = client.get(f"{ROOM_AMENITY_URL}/selectable", headers=admin_user.headers).json()
    admin_for_other = client.get(
        f"{ROOM_AMENITY_URL}/selectable",
        params={"organizationGuid": str(other_organization.guid)},
        headers=admin_user.headers,
    ).json()
    admin_for_unknown = client.get(f"{ROOM_AMENITY_URL}/selectable", params={"organizationGuid": str(uuid4())}, headers=admin_user.headers)

    assert [(option["name"], option["isDefault"]) for option in member_options] == [("fridge", False), ("Television", True)]
    assert [option["name"] for option in admin_defaults_only] == ["Television"]
    assert [option["name"] for option in admin_for_other] == ["Kettle", "Television"]
    assert admin_for_unknown.status_code == 404
