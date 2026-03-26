from datetime import date, datetime
from pydantic import BaseModel


class ChoreCreate(BaseModel):
    title: str
    description: str | None = None
    frequency: str = "weekly"
    assigned_to: str | None = None
    category: str | None = None
    priority: str = "medium"
    next_due: date | None = None


class ChoreUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    frequency: str | None = None
    assigned_to: str | None = None
    category: str | None = None
    priority: str | None = None
    next_due: date | None = None
    is_active: bool | None = None


class ChoreResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    frequency: str
    frequency_days: int | None = None
    assigned_to: str | None = None
    category: str | None = None
    priority: str
    next_due: date | None = None
    last_done: date | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChoreCompleteRequest(BaseModel):
    notes: str | None = None
    source: str = "manual"


class ChoreCompletionResponse(BaseModel):
    id: int
    chore_id: int
    completed_by: str | None = None
    completed_at: datetime
    notes: str | None = None
    source: str

    model_config = {"from_attributes": True}
