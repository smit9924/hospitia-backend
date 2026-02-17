from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates"

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

def render_template(name: str, data: dict) -> str:
    """
    Render an email template using Jinja2.

    Parameters
    ----------
    name : str
        Template name without file extension.
    data : dict[str, object]
        Context variables injected into the template.

    Returns
    -------
    str
        Rendered HTML content.
    """
    
    template = env.get_template(f"{name}.html")
    return template.render(**data)
