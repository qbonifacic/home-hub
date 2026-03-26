from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db, get_current_user
from backend.models.user import User
from backend.schemas.meal import RecipeCreate, RecipeUpdate, RecipeResponse
from backend.services.recipe_service import RecipeService

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("", response_model=list[RecipeResponse])
async def list_recipes(
    search: str | None = Query(None),
    tag: str | None = Query(None),
    favorites: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await RecipeService(db).list_all(search=search, tag=tag, favorites_only=favorites)


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await RecipeService(db).get(recipe_id)


@router.post("", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    data: RecipeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await RecipeService(db).create(data)


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    data: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await RecipeService(db).update(recipe_id, data)


@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await RecipeService(db).delete(recipe_id)


@router.post("/{recipe_id}/favorite", response_model=RecipeResponse)
async def toggle_favorite(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await RecipeService(db).toggle_favorite(recipe_id)
