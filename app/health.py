from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required

from .sheets import get_all_records, get_worksheet, append_row

health_bp = Blueprint('health', __name__)

CATEGORIES_ORDER = ['Fitness', 'Outdoor', 'Financial', 'Home', 'Social']
CATEGORY_ICONS = {
    'Fitness': 'bi-heart-pulse',
    'Outdoor': 'bi-tree',
    'Financial': 'bi-cash-stack',
    'Home': 'bi-hammer',
    'Social': 'bi-people',
}


def _normalize(record):
    return {k.lower().replace(' ', '_'): v for k, v in record.items()}


def _parse_progress(progress_str):
    """Parse progress string like '3/12' or '75%' into a 0-100 int."""
    s = str(progress_str).strip()
    if not s or s == '—':
        return 0
    if '%' in s:
        try:
            return min(100, max(0, int(s.replace('%', '').strip())))
        except ValueError:
            return 0
    if '/' in s:
        parts = s.split('/')
        try:
            num, denom = float(parts[0]), float(parts[1])
            if denom == 0:
                return 0
            return min(100, max(0, int(num / denom * 100)))
        except (ValueError, IndexError):
            return 0
    return 0


def _get_goals():
    try:
        records = get_all_records('Goals')
    except Exception:
        return []
    goals = []
    for i, r in enumerate(records):
        g = _normalize(r)
        g['row_index'] = i + 2  # sheet rows are 1-indexed + header
        g['progress_pct'] = _parse_progress(g.get('progress', ''))
        status = g.get('status', '').strip().lower()
        if status == 'completed':
            g['progress_pct'] = 100
            g['badge_class'] = 'bg-success'
            g['badge_text'] = 'Done'
        elif status == 'in progress':
            g['badge_class'] = 'bg-primary'
            g['badge_text'] = 'In Progress'
        else:
            g['badge_class'] = 'bg-secondary'
            g['badge_text'] = 'Not Started'
        goals.append(g)
    return goals


@health_bp.route('/goals')
@login_required
def index():
    goals = _get_goals()
    # Group by category
    grouped = {}
    for g in goals:
        cat = g.get('category', 'Other').strip()
        grouped.setdefault(cat, []).append(g)

    # Order categories
    ordered = []
    for cat in CATEGORIES_ORDER:
        if cat in grouped:
            ordered.append((cat, grouped.pop(cat)))
    for cat, items in grouped.items():
        ordered.append((cat, items))

    # Stats
    total = len(goals)
    completed = sum(1 for g in goals if g.get('badge_text') == 'Done')
    in_progress = sum(1 for g in goals if g.get('badge_text') == 'In Progress')
    overall_pct = int(sum(g['progress_pct'] for g in goals) / total) if total else 0

    return render_template(
        'health.html',
        grouped=ordered,
        icons=CATEGORY_ICONS,
        total=total,
        completed=completed,
        in_progress=in_progress,
        overall_pct=overall_pct,
    )


@health_bp.route('/goals/update/<int:row_index>', methods=['POST'])
@login_required
def update_goal(row_index):
    progress = request.form.get('progress', '').strip()
    status = request.form.get('status', '').strip()
    try:
        ws = get_worksheet('Goals')
        if progress:
            ws.update_cell(row_index, 4, progress)  # Column D = Progress
        if status:
            ws.update_cell(row_index, 5, status)    # Column E = Status
    except Exception:
        pass
    return redirect(url_for('health.index'))
