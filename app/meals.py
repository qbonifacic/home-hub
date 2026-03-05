import json
import re
from datetime import date

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

from .sheets import get_all_records, get_worksheet

meals_bp = Blueprint('meals', __name__)

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Keywords that suggest non-keto meals
NON_KETO_KEYWORDS = [
    'rice', 'pasta', 'bread', 'pancake', 'waffle', 'oatmeal', 'bagel', 'muffin',
    'tortilla', 'wrap', 'sandwich', 'burger', 'bun', 'potato', 'fries', 'chips',
    'sugar', 'juice', 'soda', 'beer', 'wine', 'fruit juice', 'smoothie', 'granola',
    'cereal', 'corn', 'bean', 'lentil', 'pea', 'noodle', 'udon', 'ramen',
    'cookie', 'cake', 'brownie', 'donut', 'pie', 'ice cream', 'candy',
    'honey', 'maple syrup', 'agave', 'banana', 'grape', 'mango', 'orange juice',
    'cracker', 'pretzel', 'popcorn',
]

KETO_SAFE_KEYWORDS = [
    'almond flour', 'coconut flour', 'keto', 'sugar-free', 'zero carb',
    'cauliflower', 'zucchini noodle', 'lettuce wrap',
]


def is_non_keto(meal_name):
    """Flag meals that likely contain high-carb ingredients."""
    meal_lower = meal_name.lower()
    # First check if explicitly keto-safe
    for kw in KETO_SAFE_KEYWORDS:
        if kw in meal_lower:
            return False
    for kw in NON_KETO_KEYWORDS:
        if kw in meal_lower:
            return True
    return False


def _parse_sheet_date(raw):
    """Parse '2/25/2026 (Wed)' or '2/25/2026' robustly."""
    clean = re.sub(r'\s*\(.*?\)', '', str(raw)).strip()
    parts = clean.split('/')
    if len(parts) == 3:
        try:
            return date(int(parts[2]), int(parts[0]), int(parts[1]))
        except ValueError:
            pass
    return None


def _get_meal_plan():
    try:
        records = get_all_records('Weekly Meal Plan')
        plan = {day: [] for day in DAYS}
        for r in records:
            dt = _parse_sheet_date(r.get('Date', ''))
            if dt is None:
                continue
            day_name = dt.strftime('%A')
            if day_name in plan:
                for meal_type in ('Breakfast', 'Lunch', 'Dinner', 'Snack'):
                    val = str(r.get(meal_type, '')).strip()
                    if val:
                        plan[day_name].append({
                            'meal': val,
                            'meal_type': meal_type,
                            'non_keto': is_non_keto(val),
                            'date': dt.strftime('%m/%d/%Y'),
                            'row_date': r.get('Date', ''),
                        })
        return plan
    except Exception:
        return {day: [] for day in DAYS}


def _get_recipes():
    try:
        return get_all_records('Recipes')
    except Exception:
        return []


@meals_bp.route('/meals')
@login_required
def index():
    return render_template('meals.html', plan=_get_meal_plan(), days=DAYS)


@meals_bp.route('/meals/recipe/<meal_name>')
@login_required
def recipe(meal_name):
    recipes = _get_recipes()
    rec = next((r for r in recipes if r.get('meal_name', '').strip().lower() == meal_name.lower()), None)
    if rec:
        try:
            rec['ingredients'] = json.loads(rec.get('ingredients_json', '[]'))
        except (json.JSONDecodeError, TypeError):
            rec['ingredients'] = []
    return render_template('recipe.html', recipe=rec, meal_name=meal_name)


@meals_bp.route('/meals/edit', methods=['POST'])
@login_required
def edit_meal():
    """Edit a meal in the Google Sheet. POST JSON: {day, meal_type, new_meal}"""
    try:
        data = request.get_json()
        day = data.get('day', '')
        meal_type = data.get('meal_type', '')
        new_meal = data.get('new_meal', '').strip()
        row_date = data.get('row_date', '')

        if not all([day, meal_type, new_meal]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        ws = get_worksheet('Weekly Meal Plan')
        records = ws.get_all_records()
        headers = ws.row_values(1)

        # Find the row matching the date
        col_idx = None
        for i, h in enumerate(headers):
            if h.strip().lower() == meal_type.lower():
                col_idx = i + 1  # 1-indexed
                break

        if col_idx is None:
            return jsonify({'success': False, 'error': f'Column {meal_type} not found'}), 400

        # Find the row with matching date
        for i, row in enumerate(records):
            row_date_val = str(row.get('Date', '')).strip()
            # Parse both to compare dates
            dt = _parse_sheet_date(row_date_val)
            if dt is None:
                continue
            if dt.strftime('%A') == day:
                # Update this row (i+2 because 1-indexed + header row)
                ws.update_cell(i + 2, col_idx, new_meal)
                return jsonify({
                    'success': True,
                    'non_keto': is_non_keto(new_meal),
                    'new_meal': new_meal,
                })

        # If no existing row for this day, we can't add easily without knowing the date
        return jsonify({'success': False, 'error': f'No row found for {day}'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
