"""API tests for currency unit management (`/currency-unit`)."""

from uuid import uuid4

from fastapi.testclient import TestClient

from booking.types.error_codes import ErrorCodes
from tests.conftest import API_PREFIX, TestUser

CURRENCY_UNIT_URL = f"{API_PREFIX}/currency-unit"


def create_currency_unit_via_api(client: TestClient, admin: TestUser, **overrides) -> dict:
    """Create a currency unit through the API and return the response body."""
    payload = {"currencyCode": "INR", "numericCode": "356", "currencyName": "Indian Rupee", "minorUnit": 2, **overrides}
    response = client.post(f"{CURRENCY_UNIT_URL}/create", json=payload, headers=admin.headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_admin_creates_currency_unit_with_normalized_code(client: TestClient, admin_user: TestUser) -> None:
    body = create_currency_unit_via_api(client, admin_user, currencyCode=" inr ", currencyName="  Indian Rupee ")

    assert body["currencyCode"] == "INR"
    assert body["currencyName"] == "Indian Rupee"
    assert body["numericCode"] == "356"
    assert body["minorUnit"] == 2


def test_numeric_code_keeps_leading_zeros(client: TestClient, admin_user: TestUser) -> None:
    body = create_currency_unit_via_api(client, admin_user, currencyCode="AUD", numericCode="036", currencyName="Australian Dollar")

    assert body["numericCode"] == "036"


def test_minor_unit_is_optional(client: TestClient, admin_user: TestUser) -> None:
    body = create_currency_unit_via_api(client, admin_user, currencyCode="XAU", numericCode="959", currencyName="Gold", minorUnit=None)

    assert body["minorUnit"] is None


def test_invalid_currency_fields_are_rejected(client: TestClient, admin_user: TestUser) -> None:
    invalid_payloads = [
        {"currencyCode": "IN", "numericCode": "356", "currencyName": "Indian Rupee"},
        {"currencyCode": "IN1", "numericCode": "356", "currencyName": "Indian Rupee"},
        {"currencyCode": "INR", "numericCode": "35", "currencyName": "Indian Rupee"},
        {"currencyCode": "INR", "numericCode": "3a6", "currencyName": "Indian Rupee"},
        {"currencyCode": "INR", "numericCode": "356", "currencyName": "   "},
        {"currencyCode": "INR", "numericCode": "356", "currencyName": "x" * 101},
        {"currencyCode": "INR", "numericCode": "356", "currencyName": "Indian Rupee", "minorUnit": 5},
        {"currencyCode": "INR", "numericCode": "356", "currencyName": "Indian Rupee", "minorUnit": -1},
    ]
    for payload in invalid_payloads:
        response = client.post(f"{CURRENCY_UNIT_URL}/create", json=payload, headers=admin_user.headers)
        assert response.status_code == 422, payload


def test_duplicate_currency_code_or_numeric_code_is_rejected(client: TestClient, admin_user: TestUser) -> None:
    create_currency_unit_via_api(client, admin_user)

    same_currency_code = client.post(
        f"{CURRENCY_UNIT_URL}/create",
        json={"currencyCode": "inr", "numericCode": "999", "currencyName": "Copy"},
        headers=admin_user.headers,
    )
    same_numeric_code = client.post(
        f"{CURRENCY_UNIT_URL}/create",
        json={"currencyCode": "ABC", "numericCode": "356", "currencyName": "Copy"},
        headers=admin_user.headers,
    )

    assert same_currency_code.status_code == 409
    assert same_currency_code.json()["errorCode"] == ErrorCodes.CURRENCY_UNIT_ALREADY_EXISTS
    assert same_numeric_code.status_code == 409
    assert same_numeric_code.json()["message"] == "A currency unit with this numeric code already exists."


def test_admin_updates_currency_unit_keeping_its_own_codes(client: TestClient, admin_user: TestUser) -> None:
    created = create_currency_unit_via_api(client, admin_user)

    response = client.put(
        f"{CURRENCY_UNIT_URL}/create",
        json={"guid": created["guid"], "currencyCode": "INR", "numericCode": "356", "currencyName": "Rupee", "minorUnit": 2},
        headers=admin_user.headers,
    )

    assert response.status_code == 200
    assert response.json()["currencyName"] == "Rupee"
    assert response.json()["guid"] == created["guid"]


def test_update_cannot_take_codes_of_another_currency(client: TestClient, admin_user: TestUser) -> None:
    create_currency_unit_via_api(client, admin_user)
    usd = create_currency_unit_via_api(client, admin_user, currencyCode="USD", numericCode="840", currencyName="US Dollar")

    response = client.put(
        f"{CURRENCY_UNIT_URL}/create",
        json={"guid": usd["guid"], "currencyCode": "INR", "numericCode": "840", "currencyName": "US Dollar"},
        headers=admin_user.headers,
    )

    assert response.status_code == 409


def test_update_of_unknown_currency_unit_returns_not_found(client: TestClient, admin_user: TestUser) -> None:
    response = client.put(
        f"{CURRENCY_UNIT_URL}/create",
        json={"guid": str(uuid4()), "currencyCode": "INR", "numericCode": "356", "currencyName": "Indian Rupee"},
        headers=admin_user.headers,
    )

    assert response.status_code == 404
    assert response.json()["errorCode"] == ErrorCodes.CURRENCY_UNIT_NOT_FOUND


def test_deleted_currency_unit_disappears_and_its_code_can_be_reused(client: TestClient, admin_user: TestUser) -> None:
    created = create_currency_unit_via_api(client, admin_user)

    delete_response = client.delete(f"{CURRENCY_UNIT_URL}/delete", params={"guid": created["guid"]}, headers=admin_user.headers)
    assert delete_response.status_code == 204

    assert client.get(f"{CURRENCY_UNIT_URL}/{created['guid']}", headers=admin_user.headers).status_code == 404
    assert client.get(CURRENCY_UNIT_URL, headers=admin_user.headers).json()["totalCount"] == 0
    assert client.delete(f"{CURRENCY_UNIT_URL}/delete", params={"guid": created["guid"]}, headers=admin_user.headers).status_code == 404

    recreated = create_currency_unit_via_api(client, admin_user)
    assert recreated["guid"] != created["guid"]


def test_listing_searches_sorts_and_paginates(client: TestClient, admin_user: TestUser) -> None:
    create_currency_unit_via_api(client, admin_user)
    create_currency_unit_via_api(client, admin_user, currencyCode="USD", numericCode="840", currencyName="US Dollar")
    create_currency_unit_via_api(client, admin_user, currencyCode="EUR", numericCode="978", currencyName="Euro")

    first_page = client.get(CURRENCY_UNIT_URL, params={"pageSize": 2, "pageNumber": 1}, headers=admin_user.headers).json()
    assert first_page["totalCount"] == 3
    assert [item["currencyCode"] for item in first_page["items"]] == ["EUR", "INR"]

    descending = client.get(CURRENCY_UNIT_URL, params={"sortBy": "currencyName", "sortDirection": "desc"}, headers=admin_user.headers).json()
    assert [item["currencyCode"] for item in descending["items"]] == ["USD", "INR", "EUR"]

    by_name = client.get(CURRENCY_UNIT_URL, params={"searchTerm": "rupee"}, headers=admin_user.headers).json()
    by_numeric_code = client.get(CURRENCY_UNIT_URL, params={"searchTerm": "840"}, headers=admin_user.headers).json()
    assert [item["currencyCode"] for item in by_name["items"]] == ["INR"]
    assert [item["currencyCode"] for item in by_numeric_code["items"]] == ["USD"]


def test_options_are_available_to_owner_and_manager_but_management_is_admin_only(
    client: TestClient,
    admin_user: TestUser,
    owner_user: TestUser,
    manager_user: TestUser,
    customer_user: TestUser,
) -> None:
    create_currency_unit_via_api(client, admin_user, currencyCode="USD", numericCode="840", currencyName="US Dollar")
    create_currency_unit_via_api(client, admin_user)

    for user in (admin_user, owner_user, manager_user):
        options = client.get(f"{CURRENCY_UNIT_URL}/options", headers=user.headers)
        assert options.status_code == 200
        assert [option["currencyCode"] for option in options.json()] == ["INR", "USD"]

    assert client.get(f"{CURRENCY_UNIT_URL}/options", headers=customer_user.headers).status_code == 401
    for user in (owner_user, manager_user):
        assert client.get(CURRENCY_UNIT_URL, headers=user.headers).status_code == 401
        create_response = client.post(
            f"{CURRENCY_UNIT_URL}/create",
            json={"currencyCode": "GBP", "numericCode": "826", "currencyName": "Pound Sterling"},
            headers=user.headers,
        )
        assert create_response.status_code == 401


def test_requests_without_token_are_rejected(client: TestClient) -> None:
    assert client.get(f"{CURRENCY_UNIT_URL}/options").status_code == 401
