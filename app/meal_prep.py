import json
import re
from datetime import date

from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required

from .sheets import get_all_records
from .meals import _get_meal_plan, DAYS

meal_prep_bp = Blueprint('meal_prep', __name__)


def _get_recipes():
    try:
        return get_all_records('Recipes')
    except Exception:
        return []


def _recipe_for_meal(meal_name, recipes):
    """Find recipe matching meal name."""
    meal_lower = meal_name.lower().strip()
    for r in recipes:
        if r.get('meal_name', '').strip().lower() == meal_lower:
            return r
    # partial match
    for r in recipes:
        rname = r.get('meal_name', '').strip().lower()
        if rname and (rname in meal_lower or meal_lower in rname):
            return r
    return None


def _parse_minutes(time_str):
    """Parse a time estimate string into total minutes. Returns 0 if unparseable."""
    if not time_str:
        return 0
    s = str(time_str).lower()
    total = 0
    for match in re.finditer(r'(\d+)\s*(h(?:our|r)?s?|m(?:in(?:ute)?s?)?)', s):
        val = int(match.group(1))
        unit = match.group(2)
        if unit.startswith('h'):
            total += val * 60
        else:
            total += val
    # If no unit found but there's a plain number, treat as minutes
    if total == 0:
        digits = re.findall(r'\d+', s)
        if digits:
            total = int(digits[0])
    return total


def _format_total_time(minutes):
    """Format total minutes as human-readable string."""
    if minutes <= 0:
        return None
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    mins = minutes % 60
    if mins:
        return f"{hours}h {mins}m"
    return f"{hours}h"


@meal_prep_bp.route('/meal-prep')
@login_required
def index():
    plan = _get_meal_plan()
    recipes = _get_recipes()
    prepped = session.get('prepped_meals', [])

    days_data = []
    total_prep_minutes = 0

    for day in DAYS:
        meals = plan.get(day, [])
        if not meals:
            continue
        day_meals = []
        for m in meals:
            meal_name = m.get('meal', '')
            rec = _recipe_for_meal(meal_name, recipes)
            ingredients = []
            prep_steps = []
            time_estimate = ''
            has_recipe = False

            if rec:
                has_recipe = True
                try:
                    ingredients = json.loads(rec.get('ingredients_json', '[]'))
                except (json.JSONDecodeError, TypeError):
                    ingredients = []
                prep_steps_raw = rec.get('prep_steps', rec.get('steps', ''))
                if prep_steps_raw:
                    prep_steps = [s.strip() for s in str(prep_steps_raw).split('\n') if s.strip()]
                time_estimate = rec.get('time_estimate', rec.get('time', ''))
                total_prep_minutes += _parse_minutes(time_estimate)

            meal_key = f"{day}:{meal_name}"
            day_meals.append({
                'meal': meal_name,
                'meal_type': m.get('meal_type', ''),
                'ingredients': ingredients,
                'prep_steps': prep_steps,
                'time_estimate': time_estimate,
                'meal_key': meal_key,
                'prepped': meal_key in prepped,
                'has_recipe': has_recipe,
            })
        if day_meals:
            days_data.append({'day': day, 'meals': day_meals})

    total_prep_time = _format_total_time(total_prep_minutes)

    return render_template(
        'meal_prep.html',
        days_data=days_data,
        prepped=prepped,
        total_prep_time=total_prep_time,
    )


@meal_prep_bp.route('/meal-prep/toggle', methods=['POST'])
@login_required
def toggle_prepped():
    data = request.get_json()
    meal_key = data.get('meal_key', '')
    prepped = session.get('prepped_meals', [])
    if meal_key in prepped:
        prepped.remove(meal_key)
    else:
        prepped.append(meal_key)
    session['prepped_meals'] = prepped
    session.modified = True
    return jsonify({'prepped': prepped})
