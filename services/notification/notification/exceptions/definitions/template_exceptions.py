from notification.exceptions.definitions.base import NotificationBaseException


class TemplateNotFoundError(NotificationBaseException):
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


class TemplateRenderError(NotificationBaseException):
    """
    Raised when Jinja2 fails to render a template, typically due to
    missing context variables or a syntax error in the template.

    Parameters
    ----------
    template_name : str
        The template identifier that failed to render.
    original : Exception
        The underlying Jinja2 exception.
    """

    def __init__(self, template_name: str, original: Exception) -> None:
        self.template_name = template_name
        self.original = original
        super().__init__(
            message=f"Failed to render template '{template_name}': {original}",
        )
