from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any


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
    to: List[EmailStr]
    subject: str
    template: str
    data: Dict[str, Any]
