from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db, get_current_user
from backend.models.user import User
from backend.services.chore_service import ChoreService
from backend.services.meal_service import MealService
from backend.services.outdoor_service import OutdoorService
from backend.services.pantry_service import PantryService
from backend.services.home_service import HomeService
from backend.services.calendar_service import CalendarService
from backend.services.weather_service import get_weather

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


MEAL_TYPE_ORDER = {"breakfast": 0, "lunch": 1, "dinner": 2, "snack": 3}


@router.get("")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chore_svc = ChoreService(db)
    meal_svc = MealService(db)
    outdoor_svc = OutdoorService(db)
    pantry_svc = PantryService(db)
    home_svc = HomeService(db)
    cal_svc = CalendarService(db)

    # Gather data
    weather = await get_weather()
    overdue = await chore_svc.get_overdue()
    due_today = await chore_svc.get_due_today()
    todays_meals = await meal_svc.get_today()
    outdoor_week = await outdoor_svc.get_week_summary()
    expiring = await pantry_svc.get_expiring(days_ahead=7)
    maint_due = await home_svc.get_due_soon(days_ahead=14)

    # Calendar events (gracefully handle if no sources configured)
    try:
        upcoming_events = await cal_svc.get_upcoming(user.id, days=3)
    except Exception:
        upcoming_events = []

    return {
        "weather": weather,
        "overdue_chores": [
            {"id": c.id, "title": c.title, "next_due": str(c.next_due), "assigned_to": c.assigned_to, "category": c.category}
            for c in overdue
        ],
        "due_today_chores": [
            {"id": c.id, "title": c.title, "assigned_to": c.assigned_to, "category": c.category}
            for c in due_today
        ],
        "todays_meals": sorted(
            [{"id": m.id, "meal_type": m.meal_type, "meal_name": m.meal_name} for m in todays_meals],
            key=lambda x: MEAL_TYPE_ORDER.get(x["meal_type"], 9),
        ),
        "upcoming_events": [
            {"uid": e.uid, "summary": e.summary, "start": e.start.isoformat(), "source_name": e.source_name, "source_color": e.source_color}
            for e in upcoming_events[:5]
        ],
        "expiring_pantry": [
            {"id": p.id, "item_name": p.item_name, "expiration_date": str(p.expiration_date), "storage_location": p.storage_location}
            for p in expiring[:5]
        ],
        "outdoor_this_week": outdoor_week,
        "maintenance_due": [
            {"id": t.id, "title": t.title, "next_due": str(t.next_due) if t.next_due else None}
            for t in maint_due[:5]
        ],
    }
