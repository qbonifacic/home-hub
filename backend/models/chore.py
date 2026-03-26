from datetime import date, datetime

from sqlalchemy import String, Text, Date, DateTime, Integer, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Chore(Base):
    __tablename__ = "chores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    frequency: Mapped[str] = mapped_column(String(30), nullable=False, default="weekly")
    frequency_days: Mapped[int | None] = mapped_column(Integer)
    assigned_to: Mapped[str | None] = mapped_column(String(50))  # "dj", "wife", "either", "both"
    category: Mapped[str | None] = mapped_column(String(100))  # kitchen, bathroom, yard, etc.
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high
    next_due: Mapped[date | None] = mapped_column(Date)
    last_done: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# Frequency name → days mapping
FREQUENCY_DAYS = {
    "daily": 1,
    "every_other_day": 2,
    "weekly": 7,
    "biweekly": 14,
    "monthly": 30,
    "quarterly": 90,
    "yearly": 365,
    "one_time": None,
}


class ChoreCompletion(Base):
    __tablename__ = "chore_completions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chore_id: Mapped[int] = mapped_column(Integer, ForeignKey("chores.id", ondelete="CASCADE"), nullable=False)
    completed_by: Mapped[str | None] = mapped_column(String(50))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="manual")  # "manual", "q"
