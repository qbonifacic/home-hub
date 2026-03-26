from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import String, Text, Date, DateTime, Integer, Numeric, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Appliance(Base):
    __tablename__ = "appliances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))  # appliance, system, structure, furniture, outdoor
    brand: Mapped[str | None] = mapped_column(String(100))
    model_number: Mapped[str | None] = mapped_column(String(100))
    serial_number: Mapped[str | None] = mapped_column(String(100))
    purchase_date: Mapped[date | None] = mapped_column(Date)
    warranty_until: Mapped[date | None] = mapped_column(Date)
    location: Mapped[str | None] = mapped_column(String(100))  # kitchen, garage, laundry, basement
    manual_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appliance_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("appliances.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    frequency: Mapped[str | None] = mapped_column(String(30))  # monthly, quarterly, semi_annual, annual, as_needed
    frequency_days: Mapped[int | None] = mapped_column(Integer)
    next_due: Mapped[date | None] = mapped_column(Date)
    last_done: Mapped[date | None] = mapped_column(Date)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    vendor: Mapped[str | None] = mapped_column(String(255))
    vendor_phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("maintenance_tasks.id", ondelete="SET NULL"))
    appliance_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("appliances.id", ondelete="CASCADE"))
    description: Mapped[str | None] = mapped_column(Text)
    performed_by: Mapped[str | None] = mapped_column(String(100))
    performed_date: Mapped[date] = mapped_column(Date, nullable=False)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    receipt_path: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
