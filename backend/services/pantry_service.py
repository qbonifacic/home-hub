from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pantry import PantryItem
from backend.schemas.pantry import PantryItemCreate, PantryItemUpdate


class PantryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(
        self,
        location: str | None = None,
        show_consumed: bool = False,
    ) -> list[PantryItem]:
        query = select(PantryItem).order_by(
            PantryItem.expiration_date.asc().nullslast(),
            PantryItem.item_name.asc(),
        )

        if not show_consumed:
            query = query.where(PantryItem.is_consumed == False)
        if location:
            query = query.where(PantryItem.storage_location == location)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, item_id: int) -> PantryItem:
        item = await self.db.get(PantryItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Pantry item not found")
        return item

    async def create(self, data: PantryItemCreate) -> PantryItem:
        item = PantryItem(
            item_name=data.item_name,
            category=data.category,
            quantity=data.quantity,
            unit=data.unit,
            storage_location=data.storage_location,
            expiration_date=data.expiration_date,
            expiration_source=data.expiration_source,
            is_opened=data.is_opened,
            alert_days_before=data.alert_days_before,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update(self, item_id: int, data: PantryItemUpdate) -> PantryItem:
        item = await self.get(item_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete(self, item_id: int) -> dict:
        item = await self.get(item_id)
        await self.db.delete(item)
        await self.db.commit()
        return {"ok": True}

    async def mark_consumed(self, item_id: int) -> PantryItem:
        item = await self.get(item_id)
        item.is_consumed = True
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_expiring(self, days_ahead: int = 7) -> list[PantryItem]:
        """Get items expiring within N days (for dashboard alerts)."""
        cutoff = date.today() + timedelta(days=days_ahead)
        result = await self.db.execute(
            select(PantryItem).where(
                and_(
                    PantryItem.is_consumed == False,
                    PantryItem.expiration_date != None,
                    PantryItem.expiration_date <= cutoff,
                )
            ).order_by(PantryItem.expiration_date.asc())
        )
        return list(result.scalars().all())
