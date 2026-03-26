from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db, get_current_user
from backend.models.user import User
from backend.schemas.meal import (
    MealPlanCreate, MealPlanUpdate, MealPlanResponse,
    MealPlanWeekResponse, AIGenerateRequest,
)
from backend.services.meal_service import MealService

router = APIRouter(prefix="/api/meals", tags=["meals"])


@router.get("/week", response_model=MealPlanWeekResponse)
async def get_week(
    week_of: date = Query(default_factory=date.today),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    days = await MealService(db).get_week(week_of)
    return MealPlanWeekResponse(week_of=week_of, days=days)


@router.get("/today", response_model=list[MealPlanResponse])
async def get_today(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await MealService(db).get_today()


@router.post("", response_model=MealPlanResponse, status_code=201)
async def create_meal(
    data: MealPlanCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await MealService(db).create(data, user)


@router.put("/{meal_id}", response_model=MealPlanResponse)
async def update_meal(
    meal_id: int,
    data: MealPlanUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await MealService(db).update(meal_id, data)


@router.delete("/{meal_id}")
async def delete_meal(
    meal_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await MealService(db).delete(meal_id)


@router.post("/generate", response_model=list[MealPlanResponse])
async def generate_meal_plan(
    data: AIGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await MealService(db).generate_with_ai(
        start_date=data.start_date,
        user=user,
        preferences=data.preferences,
        num_days=data.num_days,
        meal_types=data.meal_types,
    )
