from datetime import date, datetime

from sqlalchemy import String, Text, Date, DateTime, Integer, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class GroceryList(Base):
    __tablename__ = "grocery_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_of: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, shopping, completed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GroceryItem(Base):
    __tablename__ = "grocery_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_id: Mapped[int] = mapped_column(Integer, ForeignKey("grocery_lists.id", ondelete="CASCADE"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="Pantry")
    quantity: Mapped[str | None] = mapped_column(String(50))
    is_purchased: Mapped[bool] = mapped_column(Boolean, default=False)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    purchased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    purchased_by: Mapped[str | None] = mapped_column(String(50))
    sprouts_url: Mapped[str | None] = mapped_column(String(500))
    wholefoods_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
