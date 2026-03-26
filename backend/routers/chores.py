from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db, get_current_user
from backend.models.user import User
from backend.schemas.chore import ChoreCreate, ChoreUpdate, ChoreResponse, ChoreCompleteRequest, ChoreCompletionResponse
from backend.services.chore_service import ChoreService

router = APIRouter(prefix="/api/chores", tags=["chores"])


@router.get("", response_model=list[ChoreResponse])
async def list_chores(
    status: str | None = Query(None, description="Filter: overdue, due_today, upcoming"),
    assigned_to: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await ChoreService(db).list_all(status=status, assigned_to=assigned_to)


@router.get("/{chore_id}", response_model=ChoreResponse)
async def get_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await ChoreService(db).get(chore_id)


@router.post("", response_model=ChoreResponse, status_code=201)
async def create_chore(
    data: ChoreCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await ChoreService(db).create(data, user)


@router.put("/{chore_id}", response_model=ChoreResponse)
async def update_chore(
    chore_id: int,
    data: ChoreUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await ChoreService(db).update(chore_id, data)


@router.delete("/{chore_id}")
async def delete_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await ChoreService(db).delete(chore_id)


@router.post("/{chore_id}/complete")
async def complete_chore(
    chore_id: int,
    data: ChoreCompleteRequest | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    notes = data.notes if data else None
    source = data.source if data else "manual"
    return await ChoreService(db).mark_complete(chore_id, user, notes=notes, source=source)


@router.get("/{chore_id}/history", response_model=list[ChoreCompletionResponse])
async def chore_history(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await ChoreService(db).get_completions(chore_id)
