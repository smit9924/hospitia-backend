# This file will contain method who will register all the custom exception
# Register method will tak FastAPI app as the argument
from fastapi import FastAPI
from auth.exceptions.definitions.validation_exceptions import (
    UserWithEmailAlreadyExistsException,
    UserWithUsernameAlreadyExistsException,
    InvalidEmailException,
)
from auth.exceptions.handlers.validation_exception_handlers import (
    user_with_email_already_exists_exception_handler,
    user_with_username_already_exists_exception_handler,
    invalid_email_exception_handler,
)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register custom validation exception handlers with the FastAPI application.

    Parameters
    ----------
    app : FastAPI
        The FastAPI application instance.

    Returns
    -------
    None
    """
    app.add_exception_handler(UserWithEmailAlreadyExistsException, user_with_email_already_exists_exception_handler)
    app.add_exception_handler(UserWithUsernameAlreadyExistsException, user_with_username_already_exists_exception_handler)
    app.add_exception_handler(InvalidEmailException, invalid_email_exception_handler)