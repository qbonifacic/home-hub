from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import String, Text, Date, DateTime, Integer, Numeric, Boolean, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class OutdoorSession(Base):
    __tablename__ = "outdoor_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM
    duration_minutes: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    activity: Mapped[str | None] = mapped_column(String(100))
    weather: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual, q
    created_by: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SavedOption(Base):
    __tablename__ = "saved_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    field: Mapped[str] = mapped_column(String(50), nullable=False)  # location, activity, weather
    value: Mapped[str] = mapped_column(String(200), nullable=False)
    use_count: Mapped[int] = mapped_column(Integer, default=1)
    last_used: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("field", "value", name="uq_saved_options_field_value"),
    )
