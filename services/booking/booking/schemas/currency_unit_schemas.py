from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BeforeValidator, Field, StringConstraints

from booking.utils.text_utils import strip_and_uppercase_text, strip_text

from .base_schemas import BaseSchema


class CurrencyUnitCreateRequest(BaseSchema):
    """
    Request payload for creating a currency unit.

    `currency_code` is normalized to uppercase, so "inr" is stored as "INR".
    `minor_unit` is the number of decimal places defined by ISO 4217
    (0 to 4); null means ISO 4217 defines none ("N.A.").
    """

    # ISO 4217 alphabetic code: three letters, stored uppercase ("inr" -> "INR").
    currency_code: Annotated[str, BeforeValidator(strip_and_uppercase_text), StringConstraints(pattern=r"^[A-Z]{3}$")]
    # ISO 4217 numeric code: exactly three digits, leading zeros kept (e.g. "036").
    numeric_code: Annotated[str, BeforeValidator(strip_text), StringConstraints(pattern=r"^[0-9]{3}$")]
    currency_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    minor_unit: int | None = Field(default=None, ge=0, le=4)


class CurrencyUnitUpdateRequest(CurrencyUnitCreateRequest):
    """
    Request payload for updating the currency unit identified by `guid`.
    Takes the same fields as `CurrencyUnitCreateRequest`.
    """

    guid: UUID


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
