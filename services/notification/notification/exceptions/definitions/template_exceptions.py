from notification.exceptions.definitions.base import BaseException


class TemplateNotFoundError(BaseException):
    """
    Raised when the requested Jinja2 template file does not exist
    in the templates directory.

    Parameters
    ----------
    template_name : str
        The template identifier that could not be resolved.
    """

    def __init__(self, template_name: str) -> None:
        self.template_name = template_name
        super().__init__(
            message=f"Template '{template_name}' not found.",
        )
