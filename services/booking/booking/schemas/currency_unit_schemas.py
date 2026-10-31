from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BeforeValidator, Field, StringConstraints

from .base_schemas import BaseSchema


def _strip_and_uppercase(value: object) -> object:
    """Trim and uppercase text input before pattern validation runs."""
    return value.strip().upper() if isinstance(value, str) else value


def _strip(value: object) -> object:
    """Trim text input before pattern validation runs."""
    return value.strip() if isinstance(value, str) else value


# ISO 4217 alphabetic code: three letters, stored uppercase ("inr" -> "INR").
CurrencyCode = Annotated[
    str,
    BeforeValidator(_strip_and_uppercase),
    StringConstraints(pattern=r"^[A-Z]{3}$"),
]
# ISO 4217 numeric code: exactly three digits, leading zeros kept (e.g. "036").
CurrencyNumericCode = Annotated[
    str,
    BeforeValidator(_strip),
    StringConstraints(pattern=r"^[0-9]{3}$"),
]
CurrencyName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class CurrencyUnitUpsertRequest(BaseSchema):
    """
    Request payload for creating or updating a currency unit.

    When `guid` is omitted (or null), a new currency unit is created.
    When `guid` is present, the existing currency unit identified by that
    guid is updated.

    `currency_code` is normalized to uppercase, so "inr" is stored as "INR".
    `minor_unit` is the number of decimal places defined by ISO 4217
    (0 to 4); null means ISO 4217 defines none ("N.A.").
    """

    guid: UUID | None = None
    currency_code: CurrencyCode
    numeric_code: CurrencyNumericCode
    currency_name: CurrencyName
    minor_unit: int | None = Field(default=None, ge=0, le=4)


class CurrencyUnitResponse(BaseSchema):
    guid: UUID
    currency_code: str
    numeric_code: str
    currency_name: str
    minor_unit: int | None
    created_at: datetime
    updated_at: datetime


class CurrencyUnitOption(BaseSchema):
    """
    Compact currency unit used to fill currency drop-downs (e.g. the room
    type cost field).
    """

    guid: UUID
    currency_code: str
    currency_name: str
    minor_unit: int | None


class CurrencyUnitListQueryParams(BaseSchema):
    """
    Query parameters for the paginated currency unit listing endpoint.
    `search_term` matches the currency code, numeric code or name.
    """

    search_term: str | None = None
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Literal["currencyCode", "numericCode", "currencyName", "createdAt", "updatedAt"] = "currencyCode"
    sort_direction: Literal["asc", "desc"] = "asc"
    page_number: int = Field(default=1, ge=1)


class CurrencyUnitListResponse(BaseSchema):
    items: list[CurrencyUnitResponse]
    total_count: int
    page_number: int
    page_size: int
