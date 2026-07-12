class BaseException(Exception):
    """
    Base class for all custom application exceptions.

    This class serves as a common parent for all custom exceptions used in the application.
    It extends Python's built-in Exception class and is designed to be compatible with
    FastAPI's exception handling mechanism.

    Having a shared base exception allows us to apply common behavior, attributes,
    or handling logic across all custom exceptions in a single place in the future.
    """

    def __init__(self,  message: str) -> None:
        self.message = message
        super().__init__(message)
