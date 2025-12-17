# This file will contain all the exceptions related to the validation
from auth.exceptions.definitions.base import BaseException


class UserWithEmailAlreadyExistsException(BaseException):
    def __init__(self, message: str = "User with given email already exists.") -> None:
        self.message = message


class UserWithUsernameAlreadyExistsException(BaseException):
    def __init__(self, message: str = "User with given username alreadt exists.") -> None:
        self.message = message


class InvalidEmailException(BaseException):
    def __init__(self, message: str = "Invalid email.") -> None:
        self.message = message