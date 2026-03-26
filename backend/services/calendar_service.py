from datetime import datetime, timedelta, date
import asyncio
import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import caldav

from backend.models.calendar import CalendarSource
from backend.models.user import User
from backend.schemas.calendar import CalendarSourceCreate, CalendarSourceUpdate, CalendarEvent

logger = logging.getLogger(__name__)


class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_sources(self, user_id: int) -> list[CalendarSource]:
        result = await self.db.execute(
            select(CalendarSource).where(CalendarSource.user_id == user_id)
        )
        return list(result.scalars().all())

    async def create_source(self, data: CalendarSourceCreate, user: User) -> CalendarSource:
        source = CalendarSource(
            user_id=user.id,
            provider=data.provider,
            name=data.name,
            caldav_url=data.caldav_url,
            username=data.username,
            password=data.password,
            color=data.color,
        )
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def update_source(self, source_id: int, data: CalendarSourceUpdate, user: User) -> CalendarSource:
        source = await self.db.get(CalendarSource, source_id)
        if not source or source.user_id != user.id:
            raise HTTPException(status_code=404, detail="Calendar source not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(source, key, value)

        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def delete_source(self, source_id: int, user: User) -> dict:
        source = await self.db.get(CalendarSource, source_id)
        if not source or source.user_id != user.id:
            raise HTTPException(status_code=404, detail="Calendar source not found")
        await self.db.delete(source)
        await self.db.commit()
        return {"ok": True}

    async def get_events(
        self,
        user_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[CalendarEvent]:
        """Fetch events from all active CalDAV sources for a user."""
        if start is None:
            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if end is None:
            end = start + timedelta(days=7)

        sources = await self.list_sources(user_id)
        active_sources = [s for s in sources if s.is_active]

        if not active_sources:
            return []

        all_events: list[CalendarEvent] = []
        for source in active_sources:
            try:
                events = await asyncio.to_thread(
                    self._fetch_caldav_events, source, start, end
                )
                all_events.extend(events)
            except Exception as e:
                logger.warning(f"Failed to fetch from {source.name}: {e}")

        # Sort by start time
        all_events.sort(key=lambda e: e.start)
        return all_events

    def _fetch_caldav_events(
        self, source: CalendarSource, start: datetime, end: datetime
    ) -> list[CalendarEvent]:
        """Synchronous CalDAV fetch (runs in thread pool)."""
        events: list[CalendarEvent] = []

        try:
            client = caldav.DAVClient(
                url=source.caldav_url,
                username=source.username,
                password=source.password,
            )
            principal = client.principal()
            calendars = principal.calendars()

            for cal in calendars:
                try:
                    results = cal.date_search(start=start, end=end, expand=True)
                    for event in results:
                        try:
                            vevent = event.vobject_instance.vevent
                            summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else "Untitled"
                            uid = str(vevent.uid.value) if hasattr(vevent, 'uid') else ""

                            dtstart = vevent.dtstart.value
                            dtend = vevent.dtend.value if hasattr(vevent, 'dtend') else None

                            # Check if it's an all-day event
                            all_day = isinstance(dtstart, date) and not isinstance(dtstart, datetime)

                            if all_day:
                                dtstart = datetime.combine(dtstart, datetime.min.time())
                                if dtend and isinstance(dtend, date) and not isinstance(dtend, datetime):
                                    dtend = datetime.combine(dtend, datetime.min.time())

                            location = str(vevent.location.value) if hasattr(vevent, 'location') else None
                            description = str(vevent.description.value) if hasattr(vevent, 'description') else None

                            events.append(CalendarEvent(
                                uid=uid,
                                summary=summary,
                                start=dtstart,
                                end=dtend,
                                location=location,
                                description=description,
                                source_name=source.name,
                                source_color=source.color,
                                all_day=all_day,
                            ))
                        except Exception as e:
                            logger.debug(f"Failed to parse event: {e}")
                except Exception as e:
                    logger.debug(f"Failed to search calendar: {e}")

        except Exception as e:
            logger.warning(f"CalDAV connection failed for {source.name}: {e}")

        return events

    async def get_upcoming(self, user_id: int, days: int = 3) -> list[CalendarEvent]:
        """Get upcoming events for the dashboard."""
        now = datetime.now()
        end = now + timedelta(days=days)
        return await self.get_events(user_id, start=now, end=end)
