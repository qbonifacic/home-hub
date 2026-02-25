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
        records = get_all_records('MealPlan')
        today_str = date.today().strftime('%A')
        return [r for r in records if r.get('day', '').strip().lower() == today_str.lower()]
    except Exception:
        return []


def _overdue_chores():
    try:
        records = get_all_records('Chores')
        today = date.today()
        overdue = []
        for r in records:
            next_due = r.get('next_due', '')
            if next_due:
                try:
                    due = datetime.strptime(str(next_due), '%Y-%m-%d').date()
                    if due < today:
                        overdue.append(r)
                except ValueError:
                    pass
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
