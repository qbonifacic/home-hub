from datetime import datetime
from pydantic import BaseModel


class CalendarSourceCreate(BaseModel):
    provider: str  # proton, google, apple, generic
    name: str
    caldav_url: str
    username: str
    password: str
    color: str = "#6366f1"


class CalendarSourceUpdate(BaseModel):
    name: str | None = None
    caldav_url: str | None = None
    username: str | None = None
    password: str | None = None
    color: str | None = None
    is_active: bool | None = None


class CalendarSourceResponse(BaseModel):
    id: int
    user_id: int
    provider: str
    name: str
    caldav_url: str
    username: str
    color: str
    is_active: bool

    model_config = {"from_attributes": True}


class CalendarEvent(BaseModel):
    """Parsed calendar event from CalDAV."""
    uid: str
    summary: str
    start: datetime
    end: datetime | None = None
    location: str | None = None
    description: str | None = None
    source_name: str
    source_color: str
    all_day: bool = False
