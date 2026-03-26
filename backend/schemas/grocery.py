from datetime import date, datetime
from pydantic import BaseModel


class GroceryItemCreate(BaseModel):
    item_name: str
    category: str = "Pantry"
    quantity: str | None = None
    notes: str | None = None
    is_manual: bool = False


class GroceryItemUpdate(BaseModel):
    item_name: str | None = None
    category: str | None = None
    quantity: str | None = None
    is_purchased: bool | None = None
    notes: str | None = None


class GroceryItemResponse(BaseModel):
    id: int
    list_id: int
    item_name: str
    category: str
    quantity: str | None = None
    is_purchased: bool
    is_manual: bool
    purchased_at: datetime | None = None
    purchased_by: str | None = None
    sprouts_url: str | None = None
    wholefoods_url: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GroceryListCreate(BaseModel):
    week_of: date
    name: str | None = None


class GroceryListResponse(BaseModel):
    id: int
    week_of: date
    name: str | None = None
    status: str
    items: list[GroceryItemResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateFromMealsRequest(BaseModel):
    """Generate grocery list from a week's meal plans"""
    week_of: date
    list_name: str | None = None
