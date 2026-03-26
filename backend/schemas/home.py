from datetime import date, datetime
from pydantic import BaseModel


# ── Appliances ───────────────────────────────────────────────

class ApplianceCreate(BaseModel):
    name: str
    category: str | None = None  # Kitchen, HVAC, Plumbing, Electrical, Outdoor
    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    purchase_date: date | None = None
    warranty_until: date | None = None
    location: str | None = None
    notes: str | None = None


class ApplianceUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    purchase_date: date | None = None
    warranty_until: date | None = None
    location: str | None = None
    notes: str | None = None


class ApplianceResponse(BaseModel):
    id: int
    name: str
    category: str | None = None
    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    purchase_date: date | None = None
    warranty_until: date | None = None
    location: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Maintenance Tasks ────────────────────────────────────────

class MaintenanceTaskCreate(BaseModel):
    appliance_id: int | None = None
    title: str
    description: str | None = None
    frequency: str | None = None  # monthly, quarterly, yearly, one_time
    frequency_days: int | None = None
    next_due: date | None = None
    estimated_cost: float | None = None
    vendor: str | None = None


class MaintenanceTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    frequency: str | None = None
    frequency_days: int | None = None
    next_due: date | None = None
    estimated_cost: float | None = None
    vendor: str | None = None


class MaintenanceTaskResponse(BaseModel):
    id: int
    appliance_id: int | None = None
    title: str
    description: str | None = None
    frequency: str | None = None
    frequency_days: int | None = None
    next_due: date | None = None
    last_done: date | None = None
    estimated_cost: float | None = None
    vendor: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Maintenance Logs ─────────────────────────────────────────

class MaintenanceLogCreate(BaseModel):
    task_id: int | None = None
    appliance_id: int | None = None
    performed_date: date
    cost: float | None = None
    notes: str | None = None
    vendor: str | None = None


class MaintenanceLogResponse(BaseModel):
    id: int
    task_id: int | None = None
    appliance_id: int | None = None
    performed_date: date
    cost: float | None = None
    notes: str | None = None
    vendor: str | None = None
    receipt_path: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
