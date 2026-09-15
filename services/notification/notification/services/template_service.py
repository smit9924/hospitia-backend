import logging
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

log = logging.getLogger(__name__)

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

    log.info("Rendering template template_name=%s", template_name)

    try:
        template = env.get_template(template_name)
        rendered = template.render(**data)
    except (
        TemplateNotFound,
        UndefinedError
    ) as ex:
        log.error("Template rendering failed template_name=%s", template_name)
        raise TemplateNotFoundError(template_name) from ex

    log.info("Template rendered template_name=%s", template_name)
    return rendered
