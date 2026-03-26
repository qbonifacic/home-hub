from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db, get_current_user
from backend.models.user import User
from backend.schemas.pantry import PantryItemCreate, PantryItemUpdate, PantryItemResponse
from backend.services.pantry_service import PantryService

router = APIRouter(prefix="/api/pantry", tags=["pantry"])


@router.get("", response_model=list[PantryItemResponse])
async def list_pantry(
    location: str | None = Query(None),
    show_consumed: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await PantryService(db).list_all(location=location, show_consumed=show_consumed)


@router.get("/expiring", response_model=list[PantryItemResponse])
async def get_expiring(
    days: int = Query(7),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await PantryService(db).get_expiring(days_ahead=days)


@router.get("/{item_id}", response_model=PantryItemResponse)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await PantryService(db).get(item_id)


@router.post("", response_model=PantryItemResponse, status_code=201)
async def create_item(
    data: PantryItemCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await PantryService(db).create(data)


@router.put("/{item_id}", response_model=PantryItemResponse)
async def update_item(
    item_id: int,
    data: PantryItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await PantryService(db).update(item_id, data)


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await PantryService(db).delete(item_id)


@router.post("/{item_id}/consumed", response_model=PantryItemResponse)
async def mark_consumed(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await PantryService(db).mark_consumed(item_id)
