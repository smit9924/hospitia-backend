from typing import Any, Literal

from sqlalchemy import ColumnElement
from sqlmodel import col
from sqlmodel.sql.expression import SelectOfScalar


def apply_sorting_and_pagination[T](
    *,
    statement: SelectOfScalar[T],
    sort_column: Any,
    sort_direction: Literal["asc", "desc"],
    page_number: int,
    page_size: int,
) -> SelectOfScalar[T]:
    """Order a listing query and limit it to one page.

    Shared by the paginated listing repositories so every listing sorts
    and pages the same way.

    Parameters
    ----------
    statement : SelectOfScalar[T]
        Select statement with all filters already applied.
    sort_column : Any
        Model column (or SQL expression) to order by.
    sort_direction : Literal["asc", "desc"]
        Sort direction.
    page_number : int
        1-based page number.
    page_size : int
        Maximum number of rows per page.

    Returns
    -------
    SelectOfScalar[T]
        The statement ordered, offset and limited to the requested page.
    """
    ordered_column: ColumnElement[Any] = col(sort_column).desc() if sort_direction == "desc" else col(sort_column).asc()
    offset = (page_number - 1) * page_size
    return statement.order_by(ordered_column).offset(offset).limit(page_size)


def build_contains_pattern(search_term: str | None) -> str | None:
    """Build a case-insensitive ``ILIKE`` pattern from a free-text search.

    Parameters
    ----------
    search_term : str | None
        Raw search text typed by the user.

    Returns
    -------
    str | None
        ``"%term%"`` for a non-blank search term, otherwise ``None`` so the
        caller can skip the filter.
    """
    trimmed_search_term = (search_term or "").strip()
    if not trimmed_search_term:
        return None
    return f"%{trimmed_search_term}%"


__all__ = [
    "apply_sorting_and_pagination",
    "build_contains_pattern",
]
