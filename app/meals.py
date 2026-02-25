import json
import re
from datetime import date

from flask import Blueprint, render_template
from flask_login import login_required

from .sheets import get_all_records

meals_bp = Blueprint('meals', __name__)

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


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
                        plan[day_name].append({'meal': val, 'meal_type': meal_type})
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
