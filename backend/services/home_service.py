from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.home import Appliance, MaintenanceTask, MaintenanceLog
from backend.schemas.home import (
    ApplianceCreate, ApplianceUpdate,
    MaintenanceTaskCreate, MaintenanceTaskUpdate,
    MaintenanceLogCreate,
)

FREQUENCY_DAYS = {
    "monthly": 30,
    "quarterly": 90,
    "semi_annual": 180,
    "yearly": 365,
    "one_time": None,
}


class HomeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Appliances ───────────────────────────────────────────

    async def list_appliances(self, category: str | None = None) -> list[Appliance]:
        query = select(Appliance).order_by(Appliance.name.asc())
        if category:
            query = query.where(Appliance.category == category)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_appliance(self, appliance_id: int) -> Appliance:
        appliance = await self.db.get(Appliance, appliance_id)
        if not appliance:
            raise HTTPException(status_code=404, detail="Appliance not found")
        return appliance

    async def create_appliance(self, data: ApplianceCreate) -> Appliance:
        appliance = Appliance(**data.model_dump())
        self.db.add(appliance)
        await self.db.commit()
        await self.db.refresh(appliance)
        return appliance

    async def update_appliance(self, appliance_id: int, data: ApplianceUpdate) -> Appliance:
        appliance = await self.get_appliance(appliance_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(appliance, key, value)
        await self.db.commit()
        await self.db.refresh(appliance)
        return appliance

    async def delete_appliance(self, appliance_id: int) -> dict:
        appliance = await self.get_appliance(appliance_id)
        await self.db.delete(appliance)
        await self.db.commit()
        return {"ok": True}

    # ── Maintenance Tasks ────────────────────────────────────

    async def list_tasks(self, appliance_id: int | None = None) -> list[MaintenanceTask]:
        query = select(MaintenanceTask).order_by(MaintenanceTask.next_due.asc().nullslast())
        if appliance_id:
            query = query.where(MaintenanceTask.appliance_id == appliance_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_task(self, task_id: int) -> MaintenanceTask:
        task = await self.db.get(MaintenanceTask, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Maintenance task not found")
        return task

    async def create_task(self, data: MaintenanceTaskCreate) -> MaintenanceTask:
        freq_days = FREQUENCY_DAYS.get(data.frequency) if data.frequency else data.frequency_days
        next_due = data.next_due or (date.today() if freq_days else None)

        task = MaintenanceTask(
            appliance_id=data.appliance_id,
            title=data.title,
            description=data.description,
            frequency=data.frequency,
            frequency_days=freq_days or data.frequency_days,
            next_due=next_due,
            estimated_cost=data.estimated_cost,
            vendor=data.vendor,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_task(self, task_id: int, data: MaintenanceTaskUpdate) -> MaintenanceTask:
        task = await self.get_task(task_id)
        update_data = data.model_dump(exclude_unset=True)

        if "frequency" in update_data:
            update_data["frequency_days"] = FREQUENCY_DAYS.get(update_data["frequency"])

        for key, value in update_data.items():
            setattr(task, key, value)

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: int) -> dict:
        task = await self.get_task(task_id)
        await self.db.delete(task)
        await self.db.commit()
        return {"ok": True}

    async def complete_task(self, task_id: int, notes: str | None = None, cost: float | None = None) -> dict:
        """Mark a maintenance task as done and advance next_due."""
        task = await self.get_task(task_id)

        # Log completion
        log = MaintenanceLog(
            task_id=task_id,
            appliance_id=task.appliance_id,
            performed_date=date.today(),
            cost=cost,
            notes=notes,
        )
        self.db.add(log)

        # Advance next_due
        task.last_done = date.today()
        if task.frequency_days:
            task.next_due = date.today() + timedelta(days=task.frequency_days)
        elif task.frequency == "one_time":
            task.next_due = None

        await self.db.commit()
        await self.db.refresh(task)

        return {
            "ok": True,
            "task_id": task.id,
            "next_due": str(task.next_due) if task.next_due else None,
        }

    # ── Maintenance Logs ─────────────────────────────────────

    async def list_logs(self, task_id: int | None = None, appliance_id: int | None = None) -> list[MaintenanceLog]:
        query = select(MaintenanceLog).order_by(MaintenanceLog.performed_date.desc())
        if task_id:
            query = query.where(MaintenanceLog.task_id == task_id)
        if appliance_id:
            query = query.where(MaintenanceLog.appliance_id == appliance_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_log(self, data: MaintenanceLogCreate) -> MaintenanceLog:
        log = MaintenanceLog(**data.model_dump())
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    # ── Dashboard helpers ────────────────────────────────────

    async def get_due_soon(self, days_ahead: int = 14) -> list[MaintenanceTask]:
        """Get maintenance tasks due within N days."""
        cutoff = date.today() + timedelta(days=days_ahead)
        result = await self.db.execute(
            select(MaintenanceTask).where(
                and_(
                    MaintenanceTask.next_due != None,
                    MaintenanceTask.next_due <= cutoff,
                )
            ).order_by(MaintenanceTask.next_due.asc())
        )
        return list(result.scalars().all())
