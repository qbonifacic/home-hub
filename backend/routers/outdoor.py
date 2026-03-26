from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db, get_current_user
from backend.models.user import User
from backend.schemas.outdoor import (
    OutdoorSessionCreate, OutdoorSessionUpdate, OutdoorSessionResponse,
    OptionsResponse, OutdoorStatsResponse,
)
from backend.services.outdoor_service import OutdoorService

router = APIRouter(prefix="/api/outdoor", tags=["outdoor"])


@router.get("/sessions", response_model=list[OutdoorSessionResponse])
async def list_sessions(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    location: str | None = Query(None),
    activity: str | None = Query(None),
    weather: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await OutdoorService(db).list_sessions(
        start_date=start_date, end_date=end_date,
        location=location, activity=activity, weather=weather,
    )


@router.get("/sessions/{session_id}", response_model=OutdoorSessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await OutdoorService(db).get(session_id)


@router.post("/sessions", response_model=OutdoorSessionResponse, status_code=201)
async def create_session(
    data: OutdoorSessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await OutdoorService(db).create(data, user)


@router.put("/sessions/{session_id}", response_model=OutdoorSessionResponse)
async def update_session(
    session_id: int,
    data: OutdoorSessionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await OutdoorService(db).update(session_id, data)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await OutdoorService(db).delete(session_id)


@router.get("/options")
async def get_options(
    field: str | None = Query(None, description="Filter by field: location, activity, weather"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await OutdoorService(db).get_options(field=field)


@router.get("/stats", response_model=OutdoorStatsResponse)
async def get_stats(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    location: str | None = Query(None),
    activity: str | None = Query(None),
    weather: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await OutdoorService(db).get_stats(
        start_date=start_date, end_date=end_date,
        location=location, activity=activity, weather=weather,
    )
