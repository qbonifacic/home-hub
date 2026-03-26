from datetime import date, datetime

from sqlalchemy import String, Text, Date, DateTime, Integer, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    ingredients: Mapped[dict | None] = mapped_column(JSONB, default=list)  # [{name, quantity, unit, category}]
    instructions: Mapped[str | None] = mapped_column(Text)
    prep_time_min: Mapped[int | None] = mapped_column(Integer)
    cook_time_min: Mapped[int | None] = mapped_column(Integer)
    servings: Mapped[int | None] = mapped_column(Integer)
    nutritional_info: Mapped[dict | None] = mapped_column(JSONB, default=dict)  # {calories, protein_g, carbs_g, fat_g}
    tags: Mapped[list | None] = mapped_column(ARRAY(String(50)))
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(20), default="manual")  # "manual", "ai"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)  # breakfast, lunch, dinner, snack
    meal_name: Mapped[str] = mapped_column(String(300), nullable=False)
    recipe_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("recipes.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(20), default="manual")  # "manual", "ai", "q"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
