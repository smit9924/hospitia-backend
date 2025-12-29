from typing import Any

from auth.exceptions.definitions.validation_exceptions import (
    PublicEmailNotAllowedException,
    UserWithEmailAlreadyExistsException,
    UserWithUsernameAlreadyExistsException,
)
from auth.exceptions.handlers.validation_exception_handlers import (
    public_email_not_allowed_exception_handler,
    user_with_email_already_exists_exception_handler,
    user_with_username_already_exists_exception_handler,
)


def get_exception_handlers() -> dict[Any, Any]:
    """
    Returns a mapping of custom exception types to their corresponding
    FastAPI exception handler callables.
    """
    return {
        PublicEmailNotAllowedException: public_email_not_allowed_exception_handler,
        UserWithEmailAlreadyExistsException: user_with_email_already_exists_exception_handler,
        UserWithUsernameAlreadyExistsException: user_with_username_already_exists_exception_handler,
    }
