from datetime import date, datetime

from sqlalchemy import String, Text, Date, DateTime, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class PantryItem(Base):
    __tablename__ = "pantry_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))  # produce, dairy, meat, pantry, etc.
    quantity: Mapped[str | None] = mapped_column(String(50))
    unit: Mapped[str | None] = mapped_column(String(50))
    storage_location: Mapped[str | None] = mapped_column(String(50))  # fridge, freezer, pantry, counter
    expiration_date: Mapped[date | None] = mapped_column(Date)
    expiration_source: Mapped[str | None] = mapped_column(String(20))  # manual, ocr_photo, estimated
    image_path: Mapped[str | None] = mapped_column(String(500))
    purchased_at: Mapped[date | None] = mapped_column(Date)
    is_opened: Mapped[bool] = mapped_column(Boolean, default=False)
    is_consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_days_before: Mapped[int] = mapped_column(Integer, default=3)
    notes: Mapped[str | None] = mapped_column(Text)
    added_by: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
