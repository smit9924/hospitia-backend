class NotificationBaseException(Exception):
    """
    Base class for all custom notification service exceptions.

    Attributes
    ----------
    message : str
        Human-readable description of the error.
    """

    def __init__(self, message:str) -> None:
        self.message = message
        super().__init__(message)
