from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db, get_current_user
from backend.models.user import User
from backend.schemas.grocery import (
    GroceryListCreate, GroceryListResponse,
    GroceryItemCreate, GroceryItemUpdate, GroceryItemResponse,
    GenerateFromMealsRequest,
)
from backend.services.grocery_service import GroceryService

router = APIRouter(prefix="/api/grocery", tags=["grocery"])


@router.get("", response_model=list[GroceryListResponse])
async def list_grocery_lists(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lists = await GroceryService(db).list_all(status=status)
    # Attach items to each list
    svc = GroceryService(db)
    result = []
    for gl in lists:
        items = await svc.get_items(gl.id)
        response = GroceryListResponse.model_validate(gl)
        response.items = [GroceryItemResponse.model_validate(i) for i in items]
        result.append(response)
    return result


@router.get("/{list_id}", response_model=GroceryListResponse)
async def get_grocery_list(
    list_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = GroceryService(db)
    gl = await svc.get(list_id)
    items = await svc.get_items(list_id)
    response = GroceryListResponse.model_validate(gl)
    response.items = [GroceryItemResponse.model_validate(i) for i in items]
    return response


@router.post("", response_model=GroceryListResponse, status_code=201)
async def create_grocery_list(
    data: GroceryListCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    gl = await GroceryService(db).create_list(data.week_of, data.name)
    return GroceryListResponse.model_validate(gl)


@router.post("/{list_id}/items", response_model=GroceryItemResponse, status_code=201)
async def add_item(
    list_id: int,
    data: GroceryItemCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GroceryService(db).add_item(list_id, data)


@router.put("/items/{item_id}", response_model=GroceryItemResponse)
async def update_item(
    item_id: int,
    data: GroceryItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GroceryService(db).update_item(item_id, data, user)


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GroceryService(db).delete_item(item_id)


@router.put("/{list_id}/status")
async def update_list_status(
    list_id: int,
    status: str = Query(..., description="active, shopping, completed"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GroceryService(db).update_list_status(list_id, status)


@router.post("/generate", response_model=GroceryListResponse)
async def generate_from_meals(
    data: GenerateFromMealsRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = GroceryService(db)
    gl = await svc.generate_from_meals(data.week_of, user, data.list_name)
    items = await svc.get_items(gl.id)
    response = GroceryListResponse.model_validate(gl)
    response.items = [GroceryItemResponse.model_validate(i) for i in items]
    return response
