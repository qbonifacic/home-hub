from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db, get_current_user
from backend.models.user import User
from backend.schemas.calendar import (
    CalendarSourceCreate, CalendarSourceUpdate, CalendarSourceResponse, CalendarEvent,
)
from backend.services.calendar_service import CalendarService

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/sources", response_model=list[CalendarSourceResponse])
async def list_sources(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await CalendarService(db).list_sources(user.id)


@router.post("/sources", response_model=CalendarSourceResponse, status_code=201)
async def create_source(
    data: CalendarSourceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await CalendarService(db).create_source(data, user)


@router.put("/sources/{source_id}", response_model=CalendarSourceResponse)
async def update_source(
    source_id: int,
    data: CalendarSourceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await CalendarService(db).update_source(source_id, data, user)


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await CalendarService(db).delete_source(source_id, user)


@router.get("/events", response_model=list[CalendarEvent])
async def get_events(
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await CalendarService(db).get_events(user.id, start=start, end=end)
