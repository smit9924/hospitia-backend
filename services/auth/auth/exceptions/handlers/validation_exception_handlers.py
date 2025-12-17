from fastapi import Request
from fastapi.responses import JSONResponse
from auth.exceptions.definitions.validation_exceptions import (
    UserWithEmailAlreadyExistsException,
    UserWithUsernameAlreadyExistsException,
    InvalidEmailException,
)

def  user_with_email_already_exists_exception_handler(request: Request, exc: UserWithEmailAlreadyExistsException):
    return JSONResponse({"error": exc.message}, status_code=401)


def user_with_username_already_exists_exception_handler(request: Request, exc: UserWithUsernameAlreadyExistsException):
    pass


def invalid_email_exception_handler(request: Request, exc: InvalidEmailException) -> None:
    pass