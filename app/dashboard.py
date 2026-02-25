from datetime import datetime, date

import requests
from flask import Blueprint, render_template
from flask_login import login_required

from .sheets import get_all_records
from .caldav_helper import get_week_events

dashboard_bp = Blueprint('dashboard', __name__)


def _get_weather():
    try:
        r = requests.get('https://wttr.in/Fort+Collins?format=j1', timeout=5)
        data = r.json()
        cur = data['current_condition'][0]
        return {
            'temp_f': cur['temp_F'],
            'desc': cur['weatherDesc'][0]['value'],
            'humidity': cur['humidity'],
            'feels_like': cur['FeelsLikeF'],
        }
    except Exception:
        return None


def _todays_meals():
    try:
        records = get_all_records('Weekly Meal Plan')
        today = date.today()
        for r in records:
            date_str = str(r.get('Date', '')).strip()
            for fmt in ('%m/%d/%Y', '%-m/%-d/%Y', '%Y-%m-%d'):
                try:
                    if datetime.strptime(date_str, fmt).date() == today:
                        meals = []
                        for meal_type in ('Breakfast', 'Lunch', 'Dinner', 'Snack'):
                            val = r.get(meal_type, '').strip()
                            if val:
                                meals.append({'meal_type': meal_type, 'meal': val})
                        return meals
                except ValueError:
                    continue
        return []
    except Exception:
        return []


def _overdue_chores():
    try:
        records = get_all_records('Chores')
        today = date.today()
        overdue = []
        for r in records:
            next_due = str(r.get('Next Due', r.get('next_due', ''))).strip()
            if next_due:
                for fmt in ('%m/%d/%Y', '%-m/%-d/%Y', '%Y-%m-%d'):
                    try:
                        due = datetime.strptime(next_due, fmt).date()
                        if due < today:
                            overdue.append(r)
                        break
                    except ValueError:
                        continue
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
