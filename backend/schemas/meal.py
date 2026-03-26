from datetime import date, datetime
from pydantic import BaseModel


# ── Recipes ──────────────────────────────────────────────────

class IngredientItem(BaseModel):
    name: str
    quantity: str | None = None
    unit: str | None = None
    category: str | None = None


class RecipeCreate(BaseModel):
    name: str
    description: str | None = None
    ingredients: list[IngredientItem] = []
    instructions: str | None = None
    prep_time_min: int | None = None
    cook_time_min: int | None = None
    servings: int | None = None
    nutritional_info: dict | None = None
    tags: list[str] = []
    image_url: str | None = None
    is_favorite: bool = False
    source: str = "manual"


class RecipeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    ingredients: list[IngredientItem] | None = None
    instructions: str | None = None
    prep_time_min: int | None = None
    cook_time_min: int | None = None
    servings: int | None = None
    nutritional_info: dict | None = None
    tags: list[str] | None = None
    image_url: str | None = None
    is_favorite: bool | None = None


class RecipeResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    ingredients: list[dict] | None = None
    instructions: str | None = None
    prep_time_min: int | None = None
    cook_time_min: int | None = None
    servings: int | None = None
    nutritional_info: dict | None = None
    tags: list[str] | None = None
    image_url: str | None = None
    is_favorite: bool
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Meal Plans ───────────────────────────────────────────────

class MealPlanCreate(BaseModel):
    plan_date: date
    meal_type: str  # breakfast, lunch, dinner, snack
    meal_name: str
    recipe_id: int | None = None
    notes: str | None = None
    source: str = "manual"


class MealPlanUpdate(BaseModel):
    meal_name: str | None = None
    meal_type: str | None = None
    recipe_id: int | None = None
    notes: str | None = None


class MealPlanResponse(BaseModel):
    id: int
    plan_date: date
    meal_type: str
    meal_name: str
    recipe_id: int | None = None
    notes: str | None = None
    created_by: str | None = None
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MealPlanWeekResponse(BaseModel):
    """7-day meal plan grid"""
    week_of: date
    days: dict[str, list[MealPlanResponse]]  # "2026-03-11": [...]


class AIGenerateRequest(BaseModel):
    start_date: date
    preferences: str | None = None  # e.g. "healthy", "kid-friendly", "quick meals"
    num_days: int = 7
    meal_types: list[str] = ["breakfast", "lunch", "dinner"]
