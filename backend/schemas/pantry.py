from datetime import date, datetime
from pydantic import BaseModel


class PantryItemCreate(BaseModel):
    item_name: str
    category: str | None = None
    quantity: str | None = None
    unit: str | None = None
    storage_location: str = "Pantry"  # Pantry, Fridge, Freezer
    expiration_date: date | None = None
    expiration_source: str | None = None  # manual, ocr
    is_opened: bool = False
    alert_days_before: int = 3


class PantryItemUpdate(BaseModel):
    item_name: str | None = None
    category: str | None = None
    quantity: str | None = None
    unit: str | None = None
    storage_location: str | None = None
    expiration_date: date | None = None
    is_opened: bool | None = None
    is_consumed: bool | None = None
    alert_days_before: int | None = None


class PantryItemResponse(BaseModel):
    id: int
    item_name: str
    category: str | None = None
    quantity: str | None = None
    unit: str | None = None
    storage_location: str
    expiration_date: date | None = None
    expiration_source: str | None = None
    image_path: str | None = None
    is_opened: bool
    is_consumed: bool
    alert_days_before: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
