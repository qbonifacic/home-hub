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


def _chore_status(next_due_str):
    if not next_due_str:
        return 'ok'
    try:
        due = datetime.strptime(str(next_due_str), '%Y-%m-%d').date()
    except ValueError:
        return 'ok'
    today = date.today()
    if due < today:
        return 'overdue'
    if due == today:
        return 'today'
    return 'ok'


@chores_bp.route('/chores')
@login_required
def index():
    try:
        records = get_all_records('Chores')
    except Exception:
        records = []
    for r in records:
        r['status'] = _chore_status(r.get('next_due', ''))
    return render_template('chores.html', chores=records)


@chores_bp.route('/chores/done/<int:row_index>', methods=['POST'])
@login_required
def mark_done(row_index):
    try:
        ws = get_worksheet('Chores')
        row = ws.row_values(row_index)
        today_str = date.today().strftime('%Y-%m-%d')
        freq = row[1].strip().lower() if len(row) > 1 else 'weekly'
        days = FREQ_DAYS.get(freq, 7)
        next_due = (date.today() + timedelta(days=days)).strftime('%Y-%m-%d')
        ws.update_cell(row_index, 3, today_str)
        ws.update_cell(row_index, 4, next_due)
    except Exception:
        pass
    return redirect(url_for('chores.index'))
