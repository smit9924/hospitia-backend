"""Text normalizers for request validation (used with Pydantic `BeforeValidator`)."""


def strip_text(value: object) -> object:
    """Trim surrounding whitespace from text; other values pass through unchanged.

    Parameters
    ----------
    value : object
        Raw input value.

    Returns
    -------
    object
        The trimmed text, or the value unchanged when it is not a string.
    """
    return value.strip() if isinstance(value, str) else value


def strip_and_uppercase_text(value: object) -> object:
    """Trim surrounding whitespace from text and uppercase it; other values pass through unchanged.

    Parameters
    ----------
    value : object
        Raw input value.

    Returns
    -------
    object
        The trimmed, uppercased text, or the value unchanged when it is not
        a string.
    """
    return value.strip().upper() if isinstance(value, str) else value


def blank_text_to_none(value: object) -> object:
    """Treat empty or whitespace-only text as "not provided".

    Parameters
    ----------
    value : object
        Raw input value.

    Returns
    -------
    object
        ``None`` for blank text, otherwise the value unchanged.
    """
    if isinstance(value, str) and not value.strip():
        return None
    return value
