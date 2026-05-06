from typing import Any

from pydantic import BaseModel, EmailStr


class EmailPayload(BaseModel):
    """
    Payload schema for email notifications.

    Attributes
    ----------
    to : List[EmailStr]
        List of recipient email addresses.
    subject : str
        Email subject line.
    template : str
        Template identifier used for rendering content.
    data : Dict[str, Any]
        Dynamic template variables injected during rendering.
    """
    to: list[EmailStr]
    subject: str
    template: str
    data: dict[str, Any]
