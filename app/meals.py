import json

from flask import Blueprint, render_template
from flask_login import login_required

from .sheets import get_all_records

meals_bp = Blueprint('meals', __name__)

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def _get_meal_plan():
    try:
        records = get_all_records('MealPlan')
        plan = {day: [] for day in DAYS}
        for r in records:
            day = r.get('day', '').strip()
            if day in plan:
                plan[day].append(r)
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
