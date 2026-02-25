import re
from datetime import date
from urllib.parse import quote_plus

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

from .sheets import get_all_records

shopping_bp = Blueprint('shopping', __name__)

CATEGORY_KEYWORDS = {
    'Produce': ['lettuce', 'spinach', 'kale', 'avocado', 'tomato', 'onion', 'garlic',
                'pepper', 'broccoli', 'cauliflower', 'zucchini', 'mushroom', 'celery',
                'cucumber', 'lime', 'lemon', 'cilantro', 'basil', 'jalapeño', 'cabbage',
                'asparagus', 'green bean', 'bell pepper', 'arugula', 'radish', 'berry',
                'blueberr', 'strawberr', 'raspberry', 'herb', 'mint', 'parsley'],
    'Protein': ['chicken', 'beef', 'pork', 'salmon', 'shrimp', 'turkey', 'bacon',
                'sausage', 'steak', 'ground', 'egg', 'tuna', 'lamb', 'cod', 'tilapia',
                'brisket', 'rib', 'wing', 'thigh', 'breast', 'loin', 'fillet', 'anchovy'],
    'Dairy': ['cheese', 'cream', 'butter', 'yogurt', 'milk', 'sour cream',
              'mozzarella', 'parmesan', 'cheddar', 'cream cheese', 'heavy cream',
              'half and half', 'ghee', 'brie', 'feta', 'gouda', 'ricotta'],
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


def _parse_date(raw):
    clean = re.sub(r'\s*\(.*?\)', '', str(raw)).strip()
    parts = clean.split('/')
    if len(parts) == 3:
        try:
            return date(int(parts[2]), int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            pass
    return None


def _this_weeks_meals():
    """Get all unique meal names from this week's plan."""
    try:
        records = get_all_records('Weekly Meal Plan')
    except Exception:
        return []

    today = date.today()
    meals = []
    for row in records:
        d = _parse_date(row.get('Date', ''))
        if d is None:
            continue
        # Include meals within ±3 days of today (current week window)
        if abs((d - today).days) <= 6:
            for col in ('Breakfast', 'Lunch', 'Dinner', 'Snack'):
                val = str(row.get(col, '')).strip()
                if val and val.lower() not in ('', 'none', '-', 'n/a'):
                    meals.append(val)
    return list(dict.fromkeys(meals))  # dedupe, preserve order


def _meals_to_ingredients(meal_names):
    """
    Best-effort ingredient extraction from meal names using keyword matching.
    Falls back to using the meal name itself as the shopping item.
    """
    # Common keto ingredient patterns by meal keyword
    MEAL_INGREDIENTS = {
        'scrambled egg': ['eggs', 'butter', 'salt', 'pepper'],
        'egg': ['eggs', 'butter'],
        'bacon': ['bacon'],
        'avocado': ['avocados'],
        'greek yogurt': ['full-fat Greek yogurt', 'berries'],
        'tuna': ['canned tuna', 'mayo', 'celery', 'lemon'],
        'salmon': ['salmon fillet', 'lemon', 'butter', 'garlic', 'dill'],
        'chicken': ['chicken breast', 'olive oil', 'garlic', 'lemon'],
        'ground beef': ['ground beef', 'onion', 'garlic'],
        'steak': ['ribeye steak', 'butter', 'garlic', 'rosemary'],
        'burger': ['ground beef', 'lettuce', 'tomato', 'onion', 'cheese'],
        'salad': ['mixed greens', 'olive oil', 'lemon', 'salt'],
        'soup': ['chicken broth', 'vegetables', 'herbs'],
        'broccoli': ['broccoli', 'butter', 'garlic'],
        'cauliflower': ['cauliflower', 'butter', 'cheese'],
        'cheese': ['cheese'],
        'pork': ['pork chops', 'olive oil', 'garlic'],
        'shrimp': ['shrimp', 'butter', 'garlic', 'lemon'],
        'wrap': ['lettuce wraps', 'protein', 'sauce'],
        'smoothie': ['protein powder', 'almond milk', 'berries', 'spinach'],
    }

    all_ingredients = set()
    unmatched = []

    for meal in meal_names:
        lower = meal.lower()
        matched = False
        for kw, ingredients in MEAL_INGREDIENTS.items():
            if kw in lower:
                all_ingredients.update(ingredients)
                matched = True
        if not matched:
            # Use meal name as the shopping item
            unmatched.append(meal)

    # Add unmatched meals as-is (still useful as search terms)
    for m in unmatched:
        all_ingredients.add(m)

    return sorted(all_ingredients)


def _build_list():
    meal_names = _this_weeks_meals()
    if not meal_names:
        return {}, []

    ingredients = _meals_to_ingredients(meal_names)

    grouped = {'Produce': [], 'Protein': [], 'Dairy': [], 'Pantry': []}
    for item in ingredients:
        cat = _categorize(item)
        encoded = quote_plus(item)
        grouped[cat].append({
            'name': item,
            'sprouts_url': f'https://shop.sprouts.com/search?search_term={encoded}',
            'wholefoods_url': f'https://www.wholefoodsmarket.com/search?text={encoded}',
        })

    # Remove empty categories
    grouped = {k: v for k, v in grouped.items() if v}
    return grouped, meal_names


@shopping_bp.route('/shopping')
@login_required
def index():
    groups, meal_names = _build_list()
    return render_template('shopping.html', groups=groups, meal_names=meal_names)
