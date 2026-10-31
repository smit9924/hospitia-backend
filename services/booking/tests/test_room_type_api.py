"""API tests for room type management (`/room-type`) and the delete guards it adds."""

from collections.abc import Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from booking.database.models.currency_unit import CurrencyUnit
from booking.database.models.organization import Organization
from booking.types.enums import UserType
from booking.types.error_codes import ErrorCodes
from tests.conftest import API_PREFIX, TestUser

ROOM_TYPE_URL = f"{API_PREFIX}/room-type"
ROOM_AMENITY_URL = f"{API_PREFIX}/room-amenity"


@pytest.fixture
def organization(create_organization: Callable[..., Organization], owner_user: TestUser, manager_user: TestUser) -> Organization:
    """Active organization of `owner_user` and `manager_user`."""
    return create_organization("Sunrise Guest House", [owner_user, manager_user])


@pytest.fixture
def other_owner(create_user: Callable[[UserType], TestUser]) -> TestUser:
    return create_user(UserType.OWNER)


@pytest.fixture
def other_organization(create_organization: Callable[..., Organization], other_owner: TestUser) -> Organization:
    """Active organization the test owner and manager do not belong to."""
    return create_organization("Lakeview Hostel", [other_owner])


def _create_currency_unit(session: Session, currency_code: str, numeric_code: str) -> CurrencyUnit:
    currency_unit = CurrencyUnit(currency_code=currency_code, numeric_code=numeric_code, currency_name=currency_code, minor_unit=2)
    session.add(currency_unit)
    session.commit()
    session.refresh(currency_unit)
    return currency_unit


@pytest.fixture
def inr(session: Session) -> CurrencyUnit:
    return _create_currency_unit(session, "INR", "356")


@pytest.fixture
def usd(session: Session) -> CurrencyUnit:
    return _create_currency_unit(session, "USD", "840")


@pytest.fixture
def owner_headers(owner_user: TestUser, organization: Organization) -> dict[str, str]:
    return owner_user.headers_with_active_organization(organization)


def create_amenity(client: TestClient, headers: dict[str, str], name: str, **fields) -> dict:
    response = client.post(f"{ROOM_AMENITY_URL}/create", json={"name": name, **fields}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def room_type_payload(currency_unit: CurrencyUnit, **overrides) -> dict:
    return {
        "name": "Deluxe double",
        "description": "Garden view",
        "capacity": 2,
        "costPerNight": "1500.50",
        "currencyUnitGuid": str(currency_unit.guid),
        "amenityGuids": [],
        **overrides,
    }


def create_room_type(client: TestClient, headers: dict[str, str], payload: dict) -> dict:
    response = client.post(f"{ROOM_TYPE_URL}/create", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_owner_creates_room_type_with_default_and_own_amenities(
    client: TestClient,
    admin_user: TestUser,
    owner_headers: dict[str, str],
    organization: Organization,
    inr: CurrencyUnit,
) -> None:
    geyser = create_amenity(client, admin_user.headers, "Geyser")
    fridge = create_amenity(client, owner_headers, "fridge")

    room_type = create_room_type(
        client,
        owner_headers,
        room_type_payload(inr, name="  Deluxe double ", amenityGuids=[geyser["guid"], fridge["guid"], geyser["guid"]]),
    )

    assert room_type["name"] == "Deluxe double"
    assert room_type["capacity"] == 2
    assert room_type["costPerNight"] == "1500.50"
    assert room_type["currencyUnit"]["currencyCode"] == "INR"
    assert room_type["organization"] == {"guid": str(organization.guid), "name": "Sunrise Guest House"}
    assert [amenity["name"] for amenity in room_type["amenities"]] == ["fridge", "Geyser"]


def test_cost_and_capacity_boundaries_are_accepted(client: TestClient, owner_headers: dict[str, str], inr: CurrencyUnit) -> None:
    free_room = create_room_type(client, owner_headers, room_type_payload(inr, name="Dorm", capacity=1000, costPerNight=0))
    priciest_room = create_room_type(client, owner_headers, room_type_payload(inr, name="Suite", capacity=1, costPerNight="999999999.99"))

    assert free_room["costPerNight"] == "0.00"
    assert free_room["capacity"] == 1000
    assert priciest_room["costPerNight"] == "999999999.99"


@pytest.mark.parametrize(
    "overrides",
    [
        {"capacity": 0},
        {"capacity": 1001},
        {"capacity": 2.5},
        {"capacity": "2"},
        {"costPerNight": "-0.01"},
        {"costPerNight": "1000000000.00"},
        {"costPerNight": "10.123"},
        {"costPerNight": "abc"},
        {"costPerNight": "NaN"},
        {"name": "   "},
        {"name": "x" * 101},
        {"description": "x" * 501},
        {"currencyUnitGuid": None},
        {"amenityGuids": [str(uuid4()) for _ in range(101)]},
    ],
)
def test_invalid_room_type_fields_are_rejected(
    client: TestClient,
    owner_headers: dict[str, str],
    inr: CurrencyUnit,
    overrides: dict,
) -> None:
    response = client.post(f"{ROOM_TYPE_URL}/create", json=room_type_payload(inr, **overrides), headers=owner_headers)

    assert response.status_code == 422


def test_admin_must_choose_an_existing_organization(
    client: TestClient,
    admin_user: TestUser,
    organization: Organization,
    inr: CurrencyUnit,
) -> None:
    without_organization = client.post(f"{ROOM_TYPE_URL}/create", json=room_type_payload(inr), headers=admin_user.headers)
    unknown_organization = client.post(
        f"{ROOM_TYPE_URL}/create",
        json=room_type_payload(inr, organizationGuid=str(uuid4())),
        headers=admin_user.headers,
    )
    created = create_room_type(client, admin_user.headers, room_type_payload(inr, organizationGuid=str(organization.guid)))

    assert without_organization.status_code == 400
    assert without_organization.json()["errorCode"] == ErrorCodes.ROOM_TYPE_ORGANIZATION_REQUIRED
    assert unknown_organization.status_code == 404
    assert unknown_organization.json()["errorCode"] == ErrorCodes.ORGANIZATION_NOT_FOUND
    assert created["organization"]["guid"] == str(organization.guid)


def test_member_always_creates_in_active_organization(
    client: TestClient,
    manager_user: TestUser,
    organization: Organization,
    other_organization: Organization,
    inr: CurrencyUnit,
) -> None:
    created = create_room_type(
        client,
        manager_user.headers_with_active_organization(organization),
        room_type_payload(inr, organizationGuid=str(other_organization.guid)),
    )

    assert created["organization"]["guid"] == str(organization.guid)


def test_currency_must_be_an_active_currency_unit(
    client: TestClient,
    session: Session,
    owner_headers: dict[str, str],
    inr: CurrencyUnit,
) -> None:
    unknown_currency = client.post(
        f"{ROOM_TYPE_URL}/create",
        json=room_type_payload(inr, currencyUnitGuid=str(uuid4())),
        headers=owner_headers,
    )
    inr.is_active = False
    session.add(inr)
    session.commit()
    deleted_currency = client.post(f"{ROOM_TYPE_URL}/create", json=room_type_payload(inr), headers=owner_headers)

    for response in (unknown_currency, deleted_currency):
        assert response.status_code == 404
        assert response.json()["errorCode"] == ErrorCodes.CURRENCY_UNIT_NOT_FOUND


def test_only_amenities_available_to_the_organization_can_be_selected(
    client: TestClient,
    admin_user: TestUser,
    owner_headers: dict[str, str],
    other_organization: Organization,
    inr: CurrencyUnit,
) -> None:
    foreign_amenity = create_amenity(client, admin_user.headers, "Kettle", organizationGuid=str(other_organization.guid))

    for amenity_guid in (foreign_amenity["guid"], str(uuid4())):
        response = client.post(
            f"{ROOM_TYPE_URL}/create",
            json=room_type_payload(inr, amenityGuids=[amenity_guid]),
            headers=owner_headers,
        )
        assert response.status_code == 400
        assert response.json()["errorCode"] == ErrorCodes.ROOM_TYPE_AMENITY_NOT_AVAILABLE


def test_names_are_unique_per_organization_case_insensitively(
    client: TestClient,
    owner_headers: dict[str, str],
    other_owner: TestUser,
    other_organization: Organization,
    inr: CurrencyUnit,
) -> None:
    created = create_room_type(client, owner_headers, room_type_payload(inr))

    duplicate = client.post(f"{ROOM_TYPE_URL}/create", json=room_type_payload(inr, name="DELUXE DOUBLE"), headers=owner_headers)
    assert duplicate.status_code == 409
    assert duplicate.json()["errorCode"] == ErrorCodes.ROOM_TYPE_ALREADY_EXISTS

    create_room_type(client, other_owner.headers_with_active_organization(other_organization), room_type_payload(inr))

    assert client.delete(f"{ROOM_TYPE_URL}/delete", params={"guid": created["guid"]}, headers=owner_headers).status_code == 204
    create_room_type(client, owner_headers, room_type_payload(inr, name="deluxe double"))


def test_update_replaces_fields_and_amenities_but_keeps_the_organization(
    client: TestClient,
    admin_user: TestUser,
    owner_headers: dict[str, str],
    organization: Organization,
    other_organization: Organization,
    inr: CurrencyUnit,
    usd: CurrencyUnit,
) -> None:
    geyser = create_amenity(client, admin_user.headers, "Geyser")
    fridge = create_amenity(client, owner_headers, "Fridge")
    room_type = create_room_type(client, owner_headers, room_type_payload(inr, amenityGuids=[geyser["guid"]]))
    create_room_type(client, owner_headers, room_type_payload(inr, name="Single"))

    updated = client.put(
        f"{ROOM_TYPE_URL}/create",
        json=room_type_payload(
            usd,
            guid=room_type["guid"],
            name="Deluxe twin",
            description="",
            capacity=3,
            costPerNight="99.9",
            amenityGuids=[fridge["guid"]],
            organizationGuid=str(other_organization.guid),
        ),
        headers=admin_user.headers,
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert (body["name"], body["description"], body["capacity"], body["costPerNight"]) == ("Deluxe twin", None, 3, "99.90")
    assert body["currencyUnit"]["currencyCode"] == "USD"
    assert [amenity["name"] for amenity in body["amenities"]] == ["Fridge"]
    assert body["organization"]["guid"] == str(organization.guid)

    renamed_to_sibling = client.put(
        f"{ROOM_TYPE_URL}/create",
        json=room_type_payload(inr, guid=room_type["guid"], name="single"),
        headers=owner_headers,
    )
    assert renamed_to_sibling.status_code == 409

    cleared = client.put(f"{ROOM_TYPE_URL}/create", json=room_type_payload(inr, guid=room_type["guid"], name="Deluxe twin"), headers=owner_headers)
    assert cleared.json()["amenities"] == []


def test_members_cannot_reach_other_organizations_room_types(
    client: TestClient,
    owner_headers: dict[str, str],
    other_owner: TestUser,
    other_organization: Organization,
    inr: CurrencyUnit,
) -> None:
    foreign = create_room_type(client, other_owner.headers_with_active_organization(other_organization), room_type_payload(inr))

    responses = [
        client.get(f"{ROOM_TYPE_URL}/{foreign['guid']}", headers=owner_headers),
        client.put(f"{ROOM_TYPE_URL}/create", json=room_type_payload(inr, guid=foreign["guid"]), headers=owner_headers),
        client.delete(f"{ROOM_TYPE_URL}/delete", params={"guid": foreign["guid"]}, headers=owner_headers),
    ]
    for response in responses:
        assert response.status_code == 404
        assert response.json()["errorCode"] == ErrorCodes.ROOM_TYPE_NOT_FOUND
    assert client.get(ROOM_TYPE_URL, headers=owner_headers).json()["totalCount"] == 0


def test_listing_scopes_searches_sorts_and_paginates(
    client: TestClient,
    session: Session,
    admin_user: TestUser,
    owner_headers: dict[str, str],
    other_owner: TestUser,
    other_organization: Organization,
    inr: CurrencyUnit,
) -> None:
    create_room_type(client, owner_headers, room_type_payload(inr, name="Deluxe", capacity=2, costPerNight="2500"))
    create_room_type(client, owner_headers, room_type_payload(inr, name="Dorm", capacity=8, costPerNight="300"))
    create_room_type(client, other_owner.headers_with_active_organization(other_organization), room_type_payload(inr, name="Cabin"))

    member_listing = client.get(ROOM_TYPE_URL, headers=owner_headers).json()
    assert [item["name"] for item in member_listing["items"]] == ["Deluxe", "Dorm"]

    admin_listing = client.get(ROOM_TYPE_URL, headers=admin_user.headers).json()
    assert [(item["name"], item["organization"]["name"]) for item in admin_listing["items"]] == [
        ("Cabin", "Lakeview Hostel"),
        ("Deluxe", "Sunrise Guest House"),
        ("Dorm", "Sunrise Guest House"),
    ]

    by_cost = client.get(ROOM_TYPE_URL, params={"sortBy": "costPerNight"}, headers=owner_headers).json()
    by_capacity_desc = client.get(ROOM_TYPE_URL, params={"sortBy": "capacity", "sortDirection": "desc"}, headers=owner_headers).json()
    searched = client.get(ROOM_TYPE_URL, params={"searchTerm": "dorm"}, headers=owner_headers).json()
    second_page = client.get(ROOM_TYPE_URL, params={"pageSize": 1, "pageNumber": 2}, headers=owner_headers).json()
    assert [item["name"] for item in by_cost["items"]] == ["Dorm", "Deluxe"]
    assert [item["name"] for item in by_capacity_desc["items"]] == ["Dorm", "Deluxe"]
    assert [item["name"] for item in searched["items"]] == ["Dorm"]
    assert (second_page["totalCount"], [item["name"] for item in second_page["items"]]) == (2, ["Dorm"])

    # Room types of a deleted organization disappear from the admin listing.
    other_organization.is_active = False
    session.add(other_organization)
    session.commit()
    assert client.get(ROOM_TYPE_URL, headers=admin_user.headers).json()["totalCount"] == 2


def test_deleted_room_type_is_gone(client: TestClient, owner_headers: dict[str, str], inr: CurrencyUnit) -> None:
    room_type = create_room_type(client, owner_headers, room_type_payload(inr))

    assert client.delete(f"{ROOM_TYPE_URL}/delete", params={"guid": room_type["guid"]}, headers=owner_headers).status_code == 204
    assert client.get(f"{ROOM_TYPE_URL}/{room_type['guid']}", headers=owner_headers).status_code == 404
    assert client.delete(f"{ROOM_TYPE_URL}/delete", params={"guid": room_type["guid"]}, headers=owner_headers).status_code == 404


def test_currency_amenity_and_organization_in_use_cannot_be_deleted(
    client: TestClient,
    admin_user: TestUser,
    owner_user: TestUser,
    owner_headers: dict[str, str],
    organization: Organization,
    inr: CurrencyUnit,
) -> None:
    geyser = create_amenity(client, admin_user.headers, "Geyser")
    room_type = create_room_type(client, owner_headers, room_type_payload(inr, amenityGuids=[geyser["guid"]]))

    currency_delete = client.delete(f"{API_PREFIX}/currency-unit/delete", params={"guid": str(inr.guid)}, headers=admin_user.headers)
    amenity_delete = client.delete(f"{ROOM_AMENITY_URL}/delete", params={"guid": geyser["guid"]}, headers=admin_user.headers)
    organization_delete = client.delete(f"{API_PREFIX}/organization/delete", params={"guid": str(organization.guid)}, headers=owner_user.headers)

    assert currency_delete.status_code == 409
    assert currency_delete.json()["errorCode"] == ErrorCodes.CURRENCY_UNIT_IN_USE
    assert amenity_delete.status_code == 409
    assert amenity_delete.json()["errorCode"] == ErrorCodes.ROOM_AMENITY_IN_USE
    assert organization_delete.status_code == 409
    assert organization_delete.json()["errorCode"] == ErrorCodes.ORGANIZATION_HAS_ACTIVE_DEPENDENCIES

    # Once the room type is deleted, nothing active uses them any more.
    client.delete(f"{ROOM_TYPE_URL}/delete", params={"guid": room_type["guid"]}, headers=owner_headers)
    assert client.delete(f"{ROOM_AMENITY_URL}/delete", params={"guid": geyser["guid"]}, headers=admin_user.headers).status_code == 204
    assert client.delete(f"{API_PREFIX}/currency-unit/delete", params={"guid": str(inr.guid)}, headers=admin_user.headers).status_code == 204
    assert client.delete(f"{API_PREFIX}/organization/delete", params={"guid": str(organization.guid)}, headers=owner_user.headers).status_code == 204
