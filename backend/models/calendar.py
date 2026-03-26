from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class CalendarSource(Base):
    __tablename__ = "calendar_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)  # proton, google, apple
    name: Mapped[str | None] = mapped_column(String(100))
    caldav_url: Mapped[str] = mapped_column(String(500), nullable=False)
    username: Mapped[str | None] = mapped_column(String(200))
    password: Mapped[str | None] = mapped_column(String(500))
    color: Mapped[str] = mapped_column(String(7), default="#6366f1")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
