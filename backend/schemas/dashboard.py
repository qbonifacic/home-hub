from pydantic import BaseModel


class WeatherData(BaseModel):
    temp_f: int
    desc: str
    icon: str
    humidity: int
    feels_like: int
    wind_mph: int
    high: int | None = None
    low: int | None = None


class DashboardResponse(BaseModel):
    weather: WeatherData | None = None
    overdue_chores: list = []
    due_today_chores: list = []
    todays_meals: list = []
    upcoming_events: list = []
    expiring_pantry: list = []
    outdoor_this_week: dict = {}
    maintenance_due: list = []
