from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.chore import Chore, ChoreCompletion, FREQUENCY_DAYS
from backend.models.user import User
from backend.schemas.chore import ChoreCreate, ChoreUpdate


class ChoreService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, status: str | None = None, assigned_to: str | None = None) -> list[Chore]:
        query = select(Chore).where(Chore.is_active == True).order_by(Chore.next_due.asc().nullslast())

        if assigned_to:
            query = query.where(Chore.assigned_to == assigned_to)

        result = await self.db.execute(query)
        chores = list(result.scalars().all())

        if status == "overdue":
            chores = [c for c in chores if c.next_due and c.next_due < date.today()]
        elif status == "due_today":
            chores = [c for c in chores if c.next_due and c.next_due == date.today()]
        elif status == "upcoming":
            chores = [c for c in chores if c.next_due and c.next_due > date.today()]

        return chores

    async def get(self, chore_id: int) -> Chore:
        chore = await self.db.get(Chore, chore_id)
        if not chore:
            raise HTTPException(status_code=404, detail="Chore not found")
        return chore

    async def create(self, data: ChoreCreate, user: User) -> Chore:
        freq_days = FREQUENCY_DAYS.get(data.frequency)
        next_due = data.next_due or (date.today() if freq_days else None)

        chore = Chore(
            title=data.title,
            description=data.description,
            frequency=data.frequency,
            frequency_days=freq_days,
            assigned_to=data.assigned_to,
            category=data.category,
            priority=data.priority,
            next_due=next_due,
        )
        self.db.add(chore)
        await self.db.commit()
        await self.db.refresh(chore)
        return chore

    async def update(self, chore_id: int, data: ChoreUpdate) -> Chore:
        chore = await self.get(chore_id)
        update_data = data.model_dump(exclude_unset=True)

        if "frequency" in update_data:
            update_data["frequency_days"] = FREQUENCY_DAYS.get(update_data["frequency"])

        for key, value in update_data.items():
            setattr(chore, key, value)

        await self.db.commit()
        await self.db.refresh(chore)
        return chore

    async def delete(self, chore_id: int) -> dict:
        chore = await self.get(chore_id)
        chore.is_active = False
        await self.db.commit()
        return {"ok": True}

    async def mark_complete(self, chore_id: int, user: User, notes: str | None = None, source: str = "manual") -> dict:
        chore = await self.get(chore_id)

        # Record completion
        completion = ChoreCompletion(
            chore_id=chore_id,
            completed_by=user.username,
            notes=notes,
            source=source,
        )
        self.db.add(completion)

        # Advance next_due
        chore.last_done = date.today()
        if chore.frequency_days:
            chore.next_due = date.today() + timedelta(days=chore.frequency_days)
        elif chore.frequency == "one_time":
            chore.next_due = None

        await self.db.commit()
        await self.db.refresh(chore)

        return {
            "ok": True,
            "chore_id": chore.id,
            "next_due": str(chore.next_due) if chore.next_due else None,
            "last_done": str(chore.last_done),
        }

    async def get_completions(self, chore_id: int) -> list[ChoreCompletion]:
        result = await self.db.execute(
            select(ChoreCompletion)
            .where(ChoreCompletion.chore_id == chore_id)
            .order_by(ChoreCompletion.completed_at.desc())
            .limit(20)
        )
        return list(result.scalars().all())

    async def get_overdue(self) -> list[Chore]:
        result = await self.db.execute(
            select(Chore).where(
                and_(Chore.is_active == True, Chore.next_due < date.today())
            ).order_by(Chore.next_due.asc())
        )
        return list(result.scalars().all())

    async def get_due_today(self) -> list[Chore]:
        result = await self.db.execute(
            select(Chore).where(
                and_(Chore.is_active == True, Chore.next_due == date.today())
            ).order_by(Chore.title.asc())
        )
        return list(result.scalars().all())
