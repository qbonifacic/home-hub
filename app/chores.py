from datetime import datetime, date, timedelta

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required

from .sheets import get_all_records, get_worksheet

chores_bp = Blueprint('chores', __name__)

FREQ_DAYS = {
    'daily': 1,
    'every other day': 2,
    'weekly': 7,
    'biweekly': 14,
    'monthly': 30,
}


def _parse_date(raw):
    import re
    clean = re.sub(r'\s*\(.*?\)', '', str(raw)).strip()
    for fmt in ('%m/%d/%Y', '%-m/%-d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(clean, fmt).date()
        except ValueError:
            pass
    # try splitting by /
    parts = clean.split('/')
    if len(parts) == 3:
        try:
            return date(int(parts[2]), int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            pass
    return None


def _chore_status(next_due_str):
    if not next_due_str:
        return 'ok'
    due = _parse_date(next_due_str)
    if not due:
        return 'ok'
    today = date.today()
    if due < today:
        return 'overdue'
    if due == today:
        return 'today'
    return 'ok'


def _normalize(record):
    """Normalize sheet keys: lowercase, spaces→underscores."""
    return {k.lower().replace(' ', '_'): v for k, v in record.items()}


@chores_bp.route('/chores')
@login_required
def index():
    try:
        records = get_all_records('Chores')
    except Exception:
        records = []
    normalized = [_normalize(r) for r in records]
    for r in normalized:
        r['status'] = _chore_status(r.get('next_due', ''))
    return render_template('chores.html', chores=normalized)


@chores_bp.route('/chores/done/<int:row_index>', methods=['POST'])
@login_required
def mark_done(row_index):
    try:
        ws = get_worksheet('Chores')
        row = ws.row_values(row_index)
        today_str = f"{date.today().month}/{date.today().day}/{date.today().year}"
        freq = row[1].strip().lower() if len(row) > 1 else 'weekly'
        days = FREQ_DAYS.get(freq, 7)
        nd = date.today() + timedelta(days=days)
        next_due = f"{nd.month}/{nd.day}/{nd.year}"
        ws.update_cell(row_index, 3, today_str)
        ws.update_cell(row_index, 4, next_due)
    except Exception:
        pass
    return redirect(url_for('chores.index'))
