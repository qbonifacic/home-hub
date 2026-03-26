from datetime import date, datetime, timedelta
import logging

from fastapi import HTTPException
from sqlalchemy import select, func, text, and_, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.models.outdoor import OutdoorSession, SavedOption
from backend.models.user import User
from backend.schemas.outdoor import OutdoorSessionCreate, OutdoorSessionUpdate

logger = logging.getLogger(__name__)


def _calc_duration(start_time: str, end_time: str) -> float:
    """Calculate duration in minutes, handling midnight crossing."""
    fmt = "%H:%M"
    t1 = datetime.strptime(start_time, fmt)
    t2 = datetime.strptime(end_time, fmt)
    diff = (t2 - t1).total_seconds() / 60
    if diff <= 0:
        diff += 1440  # 24 hours
    return round(diff, 1)


class OutdoorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _save_option(self, field: str, value: str | None):
        """Upsert saved option with use_count increment."""
        if not value or not value.strip():
            return
        value = value.strip()
        stmt = pg_insert(SavedOption).values(
            field=field, value=value, use_count=1
        ).on_conflict_do_update(
            constraint="uq_saved_options_field_value",
            set_={
                "use_count": SavedOption.use_count + 1,
                "last_used": func.now(),
            },
        )
        await self.db.execute(stmt)

    async def list_sessions(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        location: str | None = None,
        activity: str | None = None,
        weather: str | None = None,
    ) -> list[OutdoorSession]:
        query = select(OutdoorSession).order_by(
            OutdoorSession.session_date.desc(),
            OutdoorSession.start_time.desc(),
        )

        if start_date:
            query = query.where(OutdoorSession.session_date >= start_date)
        if end_date:
            query = query.where(OutdoorSession.session_date <= end_date)
        if location:
            query = query.where(OutdoorSession.location == location)
        if activity:
            query = query.where(OutdoorSession.activity == activity)
        if weather:
            query = query.where(OutdoorSession.weather == weather)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, session_id: int) -> OutdoorSession:
        session = await self.db.get(OutdoorSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Outdoor session not found")
        return session

    async def create(self, data: OutdoorSessionCreate, user: User) -> OutdoorSession:
        duration = _calc_duration(data.start_time, data.end_time)

        session = OutdoorSession(
            session_date=data.session_date,
            start_time=data.start_time,
            end_time=data.end_time,
            duration_minutes=duration,
            location=data.location,
            activity=data.activity,
            weather=data.weather,
            notes=data.notes,
            source=data.source,
            created_by=user.username,
        )
        self.db.add(session)

        # Save options for smart dropdowns
        await self._save_option("location", data.location)
        await self._save_option("activity", data.activity)
        await self._save_option("weather", data.weather)

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def update(self, session_id: int, data: OutdoorSessionUpdate) -> OutdoorSession:
        session = await self.get(session_id)
        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(session, key, value)

        # Recalculate duration if times changed
        if "start_time" in update_data or "end_time" in update_data:
            session.duration_minutes = _calc_duration(session.start_time, session.end_time)

        # Save updated options
        if "location" in update_data:
            await self._save_option("location", session.location)
        if "activity" in update_data:
            await self._save_option("activity", session.activity)
        if "weather" in update_data:
            await self._save_option("weather", session.weather)

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete(self, session_id: int) -> dict:
        session = await self.get(session_id)
        await self.db.delete(session)
        await self.db.commit()
        return {"ok": True}

    async def get_options(self, field: str | None = None) -> dict:
        query = select(SavedOption).order_by(SavedOption.use_count.desc())
        if field:
            query = query.where(SavedOption.field == field)
        result = await self.db.execute(query)
        options = list(result.scalars().all())

        if field:
            return {field: [{"value": o.value, "use_count": o.use_count} for o in options]}

        grouped: dict[str, list] = {"location": [], "activity": [], "weather": []}
        for o in options:
            if o.field in grouped:
                grouped[o.field].append({"value": o.value, "use_count": o.use_count})
        return grouped

    async def get_stats(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        location: str | None = None,
        activity: str | None = None,
        weather: str | None = None,
    ) -> dict:
        """Get comprehensive stats with the same filter support as list_sessions."""
        conditions = []
        if start_date:
            conditions.append(OutdoorSession.session_date >= start_date)
        if end_date:
            conditions.append(OutdoorSession.session_date <= end_date)
        if location:
            conditions.append(OutdoorSession.location == location)
        if activity:
            conditions.append(OutdoorSession.activity == activity)
        if weather:
            conditions.append(OutdoorSession.weather == weather)

        base_where = and_(*conditions) if conditions else True

        # Totals
        totals_q = select(
            func.count(OutdoorSession.id).label("total_sessions"),
            func.coalesce(func.sum(OutdoorSession.duration_minutes), 0).label("total_minutes"),
            func.coalesce(func.avg(OutdoorSession.duration_minutes), 0).label("avg_minutes"),
        ).where(base_where)
        totals_row = (await self.db.execute(totals_q)).one()
        totals = {
            "total_sessions": totals_row.total_sessions,
            "total_minutes": round(float(totals_row.total_minutes), 1),
            "avg_minutes": round(float(totals_row.avg_minutes), 1),
        }

        # By location
        loc_q = select(
            OutdoorSession.location,
            func.count(OutdoorSession.id).label("sessions"),
            func.sum(OutdoorSession.duration_minutes).label("total_minutes"),
        ).where(base_where).group_by(OutdoorSession.location).order_by(
            func.sum(OutdoorSession.duration_minutes).desc()
        )
        by_location = [
            {"location": row.location, "sessions": row.sessions, "total_minutes": round(float(row.total_minutes), 1)}
            for row in (await self.db.execute(loc_q)).all()
        ]

        # By activity
        act_label = func.coalesce(OutdoorSession.activity, "Unspecified")
        act_q = select(
            act_label.label("activity"),
            func.count(OutdoorSession.id).label("sessions"),
            func.sum(OutdoorSession.duration_minutes).label("total_minutes"),
        ).where(base_where).group_by(act_label).order_by(
            func.sum(OutdoorSession.duration_minutes).desc()
        )
        by_activity = [
            {"activity": row.activity, "sessions": row.sessions, "total_minutes": round(float(row.total_minutes), 1)}
            for row in (await self.db.execute(act_q)).all()
        ]

        # Daily
        daily_q = select(
            OutdoorSession.session_date.label("date"),
            func.sum(OutdoorSession.duration_minutes).label("total_minutes"),
            func.count(OutdoorSession.id).label("sessions"),
        ).where(base_where).group_by(OutdoorSession.session_date).order_by(
            OutdoorSession.session_date.asc()
        )
        daily = [
            {"date": str(row.date), "total_minutes": round(float(row.total_minutes), 1), "sessions": row.sessions}
            for row in (await self.db.execute(daily_q)).all()
        ]

        # Weekly (ISO week)
        week_expr = func.to_char(OutdoorSession.session_date, 'IYYY-"W"IW')
        weekly_q = select(
            week_expr.label("week"),
            func.sum(OutdoorSession.duration_minutes).label("total_minutes"),
            func.count(OutdoorSession.id).label("sessions"),
        ).where(base_where).group_by(week_expr).order_by(week_expr.asc())
        weekly = [
            {"week": row.week, "total_minutes": round(float(row.total_minutes), 1), "sessions": row.sessions}
            for row in (await self.db.execute(weekly_q)).all()
        ]

        # Monthly
        month_expr = func.to_char(OutdoorSession.session_date, 'YYYY-MM')
        monthly_q = select(
            month_expr.label("month"),
            func.sum(OutdoorSession.duration_minutes).label("total_minutes"),
            func.count(OutdoorSession.id).label("sessions"),
        ).where(base_where).group_by(month_expr).order_by(month_expr.asc())
        monthly = [
            {"month": row.month, "total_minutes": round(float(row.total_minutes), 1), "sessions": row.sessions}
            for row in (await self.db.execute(monthly_q)).all()
        ]

        return {
            "totals": totals,
            "by_location": by_location,
            "by_activity": by_activity,
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
        }

    async def get_week_summary(self) -> dict:
        """Get outdoor time for the current week (for dashboard)."""
        today = date.today()
        # Monday of current week
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        result = await self.db.execute(
            select(
                func.count(OutdoorSession.id).label("sessions"),
                func.coalesce(func.sum(OutdoorSession.duration_minutes), 0).label("total_minutes"),
            ).where(
                and_(
                    OutdoorSession.session_date >= monday,
                    OutdoorSession.session_date <= sunday,
                )
            )
        )
        row = result.one()
        total_hours = round(float(row.total_minutes) / 60, 1)

        return {
            "sessions": row.sessions,
            "total_minutes": round(float(row.total_minutes), 1),
            "total_hours": total_hours,
            "week_start": str(monday),
            "week_end": str(sunday),
        }
