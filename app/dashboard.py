import re
import sys
from datetime import datetime, date

import requests
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required

from .sheets import get_all_records
from .caldav_helper import get_week_events
from .shopping import _categorize_item, _sprouts_url, _wf_url

dashboard_bp = Blueprint('dashboard', __name__)


def _get_weather():
    # Fort Collins, CO: 40.5853, -105.0844
    try:
        r = requests.get(
            'https://api.open-meteo.com/v1/forecast'
            '?latitude=40.5853&longitude=-105.0844'
            '&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m'
            '&daily=temperature_2m_max,temperature_2m_min'
            '&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FDenver&forecast_days=1',
            timeout=8,
        )
        data = r.json()
        cur = data.get('current', {})
        daily = data.get('daily', {})
        print(f"[weather] cur={cur}", file=sys.stderr)
        wmo = {
            0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
            45: 'Foggy', 48: 'Icy fog', 51: 'Light drizzle', 53: 'Drizzle',
            61: 'Light rain', 63: 'Rain', 65: 'Heavy rain',
            71: 'Light snow', 73: 'Snow', 75: 'Heavy snow',
            80: 'Rain showers', 81: 'Showers', 82: 'Heavy showers',
            95: 'Thunderstorm', 99: 'Thunderstorm with hail',
        }
        code = cur.get('weather_code', 0)
        # Weather code to emoji
        weather_icons = {
            0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
            45: '🌫️', 48: '🌫️', 51: '🌦️', 53: '🌦️',
            61: '🌧️', 63: '🌧️', 65: '🌧️',
            71: '❄️', 73: '❄️', 75: '❄️',
            80: '🌦️', 81: '🌦️', 82: '⛈️',
            95: '⛈️', 99: '⛈️',
        }

        max_temps = daily.get('temperature_2m_max', [])
        min_temps = daily.get('temperature_2m_min', [])
        high = round(max_temps[0]) if max_temps else None
        low = round(min_temps[0]) if min_temps else None

        return {
            'temp_f': round(cur.get('temperature_2m', 0)),
            'desc': wmo.get(code, f'Code {code}'),
            'icon': weather_icons.get(code, '🌡️'),
            'humidity': cur.get('relative_humidity_2m', 0),
            'feels_like': round(cur.get('apparent_temperature', 0)),
            'wind_mph': round(cur.get('wind_speed_10m', 0)),
            'high': high,
            'low': low,
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


def _week_meal_summary():
    """Get this week's meals grouped by day for the at-a-glance view."""
    try:
        records = get_all_records('Weekly Meal Plan')
        today = date.today()
        days_data = []
        for r in records:
            d = _parse_date(r.get('Date', ''))
            if d is None:
                continue
            if abs((d - today).days) <= 6:
                meals = []
                for col in ('Breakfast', 'Lunch', 'Dinner', 'Snack'):
                    val = str(r.get(col, '')).strip()
                    if val and val.lower() not in ('', 'none', '-', 'n/a'):
                        meals.append(val)
                if meals:
                    days_data.append({
                        'day': d.strftime('%a'),
                        'date': d,
                        'meals': meals,
                        'is_today': d == today,
                    })
        days_data.sort(key=lambda x: x['date'])
        return days_data
    except Exception:
        return []


def _overdue_chores():
    try:
        records = get_all_records('Chores')
        today = date.today()
        overdue = []
        for r in records:
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


def _goals_summary():
    try:
        records = get_all_records('Goals')
        total = len(records)
        completed = sum(1 for r in records if r.get('Status', '').strip().lower() == 'completed')
        in_progress = sum(1 for r in records if r.get('Status', '').strip().lower() == 'in progress')
        return {'total': total, 'completed': completed, 'in_progress': in_progress}
    except Exception:
        return None


@dashboard_bp.route('/')
@login_required
def index():
    return render_template(
        'dashboard.html',
        today=date.today(),
        weather=_get_weather(),
        meals=_todays_meals(),
        week_meals=_week_meal_summary(),
        overdue=_overdue_chores(),
        events=_upcoming_events(),
        goals=_goals_summary(),
    )


@dashboard_bp.route('/dashboard/add-grocery', methods=['POST'])
@login_required
def add_grocery():
    """Quick-add grocery item from dashboard."""
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'No item name'}), 400

    manual_items = session.get('manual_items', [])
    category = _categorize_item(name)
    item_id = f"manual_{len(manual_items)}_{name[:20].replace(' ', '_')}"

    manual_items.append({
        'name': name,
        'category': category,
        'id': item_id,
    })
    session['manual_items'] = manual_items
    session.modified = True

    return jsonify({'success': True, 'name': name, 'category': category})
