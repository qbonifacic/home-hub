import re
from datetime import datetime, date

import requests
from flask import Blueprint, render_template
from flask_login import login_required

from .sheets import get_all_records
from .caldav_helper import get_week_events

dashboard_bp = Blueprint('dashboard', __name__)


def _get_weather():
    # Fort Collins, CO: 40.5853, -105.0844
    try:
        r = requests.get(
            'https://api.open-meteo.com/v1/forecast'
            '?latitude=40.5853&longitude=-105.0844'
            '&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code'
            '&temperature_unit=fahrenheit&wind_speed_unit=mph&forecast_days=1',
            timeout=8,
        )
        data = r.json()
        cur = data.get('current', {})
        wmo = {
            0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
            45: 'Foggy', 48: 'Icy fog', 51: 'Light drizzle', 53: 'Drizzle',
            61: 'Light rain', 63: 'Rain', 65: 'Heavy rain',
            71: 'Light snow', 73: 'Snow', 75: 'Heavy snow',
            80: 'Rain showers', 81: 'Showers', 82: 'Heavy showers',
            95: 'Thunderstorm', 99: 'Thunderstorm with hail',
        }
        code = cur.get('weather_code', 0)
        return {
            'temp_f': round(cur.get('temperature_2m', 0)),
            'desc': wmo.get(code, f'Code {code}'),
            'humidity': cur.get('relative_humidity_2m', 0),
            'feels_like': round(cur.get('apparent_temperature', 0)),
        }
    except Exception:
        return None


def _parse_date(raw):
    clean = re.sub(r'\s*\(.*?\)', '', str(raw)).strip()
    parts = clean.split('/')
    if len(parts) == 3:
        try:
            return date(int(parts[2]), int(parts[0]), int(parts[1]))
        except ValueError:
            pass
    return None


def _todays_meals():
    try:
        records = get_all_records('Weekly Meal Plan')
        today = date.today()
        for r in records:
            if _parse_date(r.get('Date', '')) == today:
                meals = []
                for meal_type in ('Breakfast', 'Lunch', 'Dinner', 'Snack'):
                    val = str(r.get(meal_type, '')).strip()
                    if val:
                        meals.append({'meal_type': meal_type, 'meal': val})
                return meals
        return []
    except Exception:
        return []


def _overdue_chores():
    try:
        records = get_all_records('Chores')
        today = date.today()
        overdue = []
        for r in records:
            # normalize keys to lowercase
            r_lower = {k.lower(): v for k, v in r.items()}
            next_due = str(r_lower.get('next due', r_lower.get('next_due', ''))).strip()
            if next_due:
                due = _parse_date(next_due)
                if due and due <= today:
                    overdue.append({
                        'task': r_lower.get('task', 'Unknown'),
                        'next_due': next_due,
                        'assigned': r_lower.get('assigned', ''),
                        'frequency': r_lower.get('frequency', ''),
                    })
        return overdue
    except Exception:
        return []


def _upcoming_events():
    try:
        events = get_week_events()
        return events[:10]
    except Exception:
        return []


@dashboard_bp.route('/')
@login_required
def index():
    return render_template(
        'dashboard.html',
        today=date.today(),
        weather=_get_weather(),
        meals=_todays_meals(),
        overdue=_overdue_chores(),
        events=_upcoming_events(),
    )
