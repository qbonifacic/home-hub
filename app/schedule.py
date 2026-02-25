from datetime import datetime, timedelta
from collections import defaultdict

from flask import Blueprint, render_template
from flask_login import login_required

from .caldav_helper import get_week_events

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/schedule')
@login_required
def index():
    events = get_week_events()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days = []
    by_date = defaultdict(list)
    for e in events:
        by_date[e['date']].append(e)
    for i in range(7):
        d = today + timedelta(days=i)
        date_str = d.strftime('%Y-%m-%d')
        days.append({
            'date': d,
            'label': d.strftime('%A %b %d'),
            'events': by_date.get(date_str, []),
        })
    return render_template('schedule.html', days=days)
