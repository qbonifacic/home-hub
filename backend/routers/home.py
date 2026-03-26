from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db, get_current_user
from backend.models.user import User
from backend.schemas.home import (
    ApplianceCreate, ApplianceUpdate, ApplianceResponse,
    MaintenanceTaskCreate, MaintenanceTaskUpdate, MaintenanceTaskResponse,
    MaintenanceLogCreate, MaintenanceLogResponse,
)
from backend.services.home_service import HomeService

router = APIRouter(prefix="/api/home", tags=["home"])


# ── Appliances ───────────────────────────────────────────────

@router.get("/appliances", response_model=list[ApplianceResponse])
async def list_appliances(
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).list_appliances(category=category)


@router.post("/appliances", response_model=ApplianceResponse, status_code=201)
async def create_appliance(
    data: ApplianceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).create_appliance(data)


@router.put("/appliances/{appliance_id}", response_model=ApplianceResponse)
async def update_appliance(
    appliance_id: int,
    data: ApplianceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).update_appliance(appliance_id, data)


@router.delete("/appliances/{appliance_id}")
async def delete_appliance(
    appliance_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).delete_appliance(appliance_id)


# ── Maintenance Tasks ────────────────────────────────────────

@router.get("/tasks", response_model=list[MaintenanceTaskResponse])
async def list_tasks(
    appliance_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).list_tasks(appliance_id=appliance_id)


@router.post("/tasks", response_model=MaintenanceTaskResponse, status_code=201)
async def create_task(
    data: MaintenanceTaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).create_task(data)


@router.put("/tasks/{task_id}", response_model=MaintenanceTaskResponse)
async def update_task(
    task_id: int,
    data: MaintenanceTaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).update_task(task_id, data)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).delete_task(task_id)


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    notes: str | None = None,
    cost: float | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).complete_task(task_id, notes=notes, cost=cost)


# ── Maintenance Logs ─────────────────────────────────────────

@router.get("/logs", response_model=list[MaintenanceLogResponse])
async def list_logs(
    task_id: int | None = Query(None),
    appliance_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).list_logs(task_id=task_id, appliance_id=appliance_id)


@router.post("/logs", response_model=MaintenanceLogResponse, status_code=201)
async def create_log(
    data: MaintenanceLogCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await HomeService(db).create_log(data)
