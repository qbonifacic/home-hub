from datetime import date, datetime
from pydantic import BaseModel


class OutdoorSessionCreate(BaseModel):
    session_date: date
    start_time: str  # HH:MM 24-hour
    end_time: str  # HH:MM 24-hour
    location: str
    activity: str | None = None
    weather: str | None = None
    notes: str | None = None
    source: str = "manual"


class OutdoorSessionUpdate(BaseModel):
    session_date: date | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    activity: str | None = None
    weather: str | None = None
    notes: str | None = None


class OutdoorSessionResponse(BaseModel):
    id: int
    session_date: date
    start_time: str
    end_time: str
    duration_minutes: float
    location: str
    activity: str | None = None
    weather: str | None = None
    notes: str | None = None
    source: str
    created_by: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SavedOptionResponse(BaseModel):
    value: str
    use_count: int


class OptionsResponse(BaseModel):
    location: list[SavedOptionResponse] = []
    activity: list[SavedOptionResponse] = []
    weather: list[SavedOptionResponse] = []


class OutdoorStatsResponse(BaseModel):
    totals: dict  # total_sessions, total_minutes, avg_minutes
    by_location: list[dict]
    by_activity: list[dict]
    daily: list[dict]
    weekly: list[dict]
    monthly: list[dict]
