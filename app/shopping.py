import json
from urllib.parse import quote_plus

from flask import Blueprint, render_template
from flask_login import login_required

from .sheets import get_all_records

shopping_bp = Blueprint('shopping', __name__)

CATEGORY_KEYWORDS = {
    'Produce': ['lettuce', 'spinach', 'kale', 'avocado', 'tomato', 'onion', 'garlic',
                'pepper', 'broccoli', 'cauliflower', 'zucchini', 'mushroom', 'celery',
                'cucumber', 'lime', 'lemon', 'cilantro', 'basil', 'jalapeño', 'cabbage',
                'asparagus', 'green bean', 'bell pepper', 'arugula', 'radish'],
    'Protein': ['chicken', 'beef', 'pork', 'salmon', 'shrimp', 'turkey', 'bacon',
                'sausage', 'steak', 'ground', 'egg', 'tuna', 'lamb', 'cod', 'tilapia'],
    'Dairy': ['cheese', 'cream', 'butter', 'yogurt', 'milk', 'sour cream',
              'mozzarella', 'parmesan', 'cheddar', 'cream cheese', 'heavy cream',
              'half and half', 'ghee'],
    'Pantry': [],
}


def _categorize(item):
    lower = item.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if cat == 'Pantry':
            continue
        for kw in keywords:
            if kw in lower:
                return cat
    return 'Pantry'


def _build_list():
    try:
        plan = get_all_records('MealPlan')
        recipes = get_all_records('Recipes')
    except Exception:
        return {}

    recipe_map = {r['meal_name'].strip().lower(): r for r in recipes if r.get('meal_name')}
    ingredients = set()

    for meal in plan:
        name = meal.get('meal', '').strip().lower()
        if name in recipe_map:
            try:
                items = json.loads(recipe_map[name].get('ingredients_json', '[]'))
                for item in items:
                    ingredients.add(str(item).strip())
            except (json.JSONDecodeError, TypeError):
                pass

    grouped = {'Produce': [], 'Protein': [], 'Dairy': [], 'Pantry': []}
    for item in sorted(ingredients):
        cat = _categorize(item)
        encoded = quote_plus(item)
        grouped[cat].append({
            'name': item,
            'sprouts_url': f'https://shop.sprouts.com/search?search_term={encoded}',
            'wholefoods_url': f'https://www.wholefoodsmarket.com/search?text={encoded}',
        })
    return grouped


@shopping_bp.route('/shopping')
@login_required
def index():
    return render_template('shopping.html', groups=_build_list())
