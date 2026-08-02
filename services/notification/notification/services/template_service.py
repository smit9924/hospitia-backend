from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateNotFound,
    select_autoescape,
)
from jinja2.exceptions import UndefinedError

from notification.exceptions.definitions.template_exceptions import (
    TemplateNotFoundError,
)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(("html", "xml")),
    undefined=StrictUndefined,
)


def render_template(
    template_name: str,
    data: dict[str, Any],
) -> str:
    """
    Render a Jinja2 template with the provided data.

    Parameters
    ----------
    template_name : str
        The name of the template file (without the .html extension).
    data : dict[str, Any]
        A dictionary containing the data to be injected into the template.

    Returns
    -------
    str
        The rendered HTML content as a string.
    """
    global template

    try:
        template = env.get_template(template_name)
        return template.render(**data)
    except (
        TemplateNotFound,
        UndefinedError
    ) as ex:
        raise TemplateNotFoundError(template_name) from ex

