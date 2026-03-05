import json
import os
import re
from datetime import date
from urllib.parse import quote_plus

import requests as http_requests

from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required

from .sheets import get_all_records

_LLM_CACHE_PATH = '/tmp/meal_ingredient_cache.json'
_LLM_BASE_URL = 'http://10.0.0.102:11434/v1'
_LLM_MODEL = 'llama3.3:70b'

shopping_bp = Blueprint('shopping', __name__)

# ─────────────────────────────────────────────
# Ingredient database — keyed to exact meal names
# category: Produce | Protein | Dairy | Pantry
# ─────────────────────────────────────────────
MEAL_INGREDIENTS = {
    "Scrambled eggs (3) with spinach, mushrooms, cheddar cheese": [
        ("eggs", "Protein"), ("fresh spinach", "Produce"), ("mushrooms", "Produce"),
        ("cheddar cheese", "Dairy"), ("butter", "Dairy"),
    ],
    "Omelet with bacon, cheese, and avocado": [
        ("eggs", "Protein"), ("bacon", "Protein"), ("avocado", "Produce"),
        ("shredded cheese", "Dairy"), ("butter", "Dairy"),
    ],
    "Keto pancakes (almond flour) with sugar-free syrup, bacon": [
        ("almond flour", "Pantry"), ("eggs", "Protein"), ("bacon", "Protein"),
        ("sugar-free syrup", "Pantry"), ("baking powder", "Pantry"), ("butter", "Dairy"),
    ],
    "Greek yogurt (full-fat) with walnuts and chia seeds": [
        ("full-fat Greek yogurt", "Dairy"), ("walnuts", "Pantry"), ("chia seeds", "Pantry"),
    ],
    "Keto smoothie (avocado, coconut milk, protein powder, spinach)": [
        ("avocado", "Produce"), ("coconut milk (canned)", "Pantry"), ("protein powder", "Pantry"),
        ("fresh spinach", "Produce"),
    ],
    "Breakfast burrito bowl (scrambled eggs, sausage, cheese, salsa, avocado)": [
        ("eggs", "Protein"), ("breakfast sausage", "Protein"), ("shredded cheese", "Dairy"),
        ("salsa (no-sugar)", "Pantry"), ("avocado", "Produce"),
    ],

    # ── Lunch ──
    "Tuna salad lettuce wraps (tuna, mayo, celery, onion)": [
        ("canned tuna", "Protein"), ("mayo", "Pantry"), ("celery", "Produce"),
        ("white onion", "Produce"), ("romaine lettuce", "Produce"),
    ],
    "Chicken Caesar salad (grilled chicken, romaine, parmesan, keto Caesar)": [
        ("chicken breast", "Protein"), ("romaine lettuce", "Produce"),
        ("parmesan cheese", "Dairy"), ("keto Caesar dressing", "Pantry"),
    ],
    "Cobb salad (eggs, bacon, avocado, chicken, blue cheese)": [
        ("eggs", "Protein"), ("bacon", "Protein"), ("chicken breast", "Protein"),
        ("avocado", "Produce"), ("blue cheese", "Dairy"), ("mixed greens", "Produce"),
        ("cherry tomatoes", "Produce"),
    ],
    "Leftover chicken with side salad": [
        ("mixed greens", "Produce"), ("olive oil", "Pantry"), ("lemon", "Produce"),
    ],
    "Leftover salmon salad with mixed greens": [
        ("mixed greens", "Produce"), ("olive oil", "Pantry"), ("lemon", "Produce"),
    ],
    "Leftover steak salad": [
        ("mixed greens", "Produce"), ("olive oil", "Pantry"), ("cherry tomatoes", "Produce"),
    ],
    "Chicken vegetable soup (bone broth, chicken, low-carb veggies)": [
        ("chicken breast", "Protein"), ("bone broth", "Pantry"), ("zucchini", "Produce"),
        ("celery", "Produce"), ("onion", "Produce"), ("garlic", "Produce"),
    ],

    # ── Dinner ──
    "Salmon with lemon butter sauce, roasted asparagus, side salad": [
        ("salmon fillet", "Protein"), ("asparagus", "Produce"), ("butter", "Dairy"),
        ("lemon", "Produce"), ("garlic", "Produce"), ("mixed greens", "Produce"),
    ],
    "Chicken thighs with skin, roasted Brussels sprouts, cauliflower mash": [
        ("chicken thighs (bone-in)", "Protein"), ("Brussels sprouts", "Produce"),
        ("cauliflower", "Produce"), ("butter", "Dairy"), ("heavy cream", "Dairy"),
        ("garlic", "Produce"),
    ],
    "Steak (ribeye) with compound butter, sautéed mushrooms, green beans": [
        ("ribeye steak", "Protein"), ("mushrooms", "Produce"), ("green beans", "Produce"),
        ("butter", "Dairy"), ("garlic", "Produce"), ("fresh herbs (rosemary/thyme)", "Produce"),
    ],
    "Pork chops with apple cider vinegar glaze, roasted cabbage, side salad": [
        ("pork chops", "Protein"), ("apple cider vinegar", "Pantry"), ("green cabbage", "Produce"),
        ("mixed greens", "Produce"), ("olive oil", "Pantry"),
    ],
    "Shrimp scampi with zucchini noodles, side salad": [
        ("large shrimp (peeled)", "Protein"), ("zucchini", "Produce"), ("butter", "Dairy"),
        ("garlic", "Produce"), ("lemon", "Produce"), ("white wine or broth", "Pantry"),
        ("mixed greens", "Produce"),
    ],
    "Beef stir-fry with broccoli, bell peppers, mushrooms (coconut aminos)": [
        ("sirloin steak (sliced)", "Protein"), ("broccoli florets", "Produce"),
        ("bell peppers", "Produce"), ("mushrooms", "Produce"), ("coconut aminos", "Pantry"),
        ("sesame oil", "Pantry"), ("garlic", "Produce"), ("ginger", "Produce"),
    ],
    "Zucchini noodles with meatballs and marinara (sugar-free sauce)": [
        ("ground beef", "Protein"), ("zucchini", "Produce"), ("sugar-free marinara", "Pantry"),
        ("parmesan cheese", "Dairy"), ("egg", "Protein"), ("garlic", "Produce"),
        ("Italian seasoning", "Pantry"),
    ],

    # ── Snacks ──
    "Hard boiled egg + olives": [
        ("eggs", "Protein"), ("olives", "Pantry"),
    ],
    "Celery + almond butter": [
        ("celery", "Produce"), ("almond butter", "Pantry"),
    ],
    "Pepperoni + fresh mozzarella": [
        ("pepperoni", "Protein"), ("fresh mozzarella", "Dairy"),
    ],
    "Pork rinds + guacamole": [
        ("pork rinds", "Pantry"), ("avocado", "Produce"), ("lime", "Produce"),
        ("onion", "Produce"), ("cilantro", "Produce"), ("jalapeño", "Produce"),
    ],
    "Walnuts + 85% dark chocolate": [
        ("walnuts", "Pantry"), ("85% dark chocolate", "Pantry"),
    ],
    "String cheese + almonds": [
        ("string cheese", "Dairy"), ("raw almonds", "Pantry"),
    ],
    "Baked Parmesan crisps": [
        ("parmesan cheese", "Dairy"),
    ],
    "Chia pudding (chia seeds, coconut milk, vanilla, berries)": [
        ("chia seeds", "Pantry"), ("coconut milk (canned)", "Pantry"),
        ("vanilla extract", "Pantry"), ("mixed berries", "Produce"),
    ],
}

# Keyword-based category detection for manually-added items
CATEGORY_KEYWORDS = {
    'Produce': [
        'apple', 'banana', 'berry', 'berries', 'grape', 'lemon', 'lime', 'orange',
        'spinach', 'lettuce', 'kale', 'arugula', 'greens', 'broccoli', 'cauliflower',
        'carrot', 'celery', 'cucumber', 'tomato', 'pepper', 'onion', 'garlic', 'ginger',
        'zucchini', 'squash', 'mushroom', 'avocado', 'asparagus', 'green bean',
        'brussels', 'cabbage', 'herb', 'cilantro', 'parsley', 'rosemary', 'thyme',
        'jalapeño', 'jalapen', 'fresh',
    ],
    'Protein': [
        'chicken', 'beef', 'steak', 'pork', 'lamb', 'turkey', 'salmon', 'tuna',
        'shrimp', 'fish', 'egg', 'bacon', 'sausage', 'ground', 'ribeye', 'sirloin',
        'pepperoni', 'meatball', 'brisket', 'chop', 'fillet', 'seafood',
    ],
    'Dairy': [
        'cheese', 'butter', 'cream', 'milk', 'yogurt', 'mozzarella', 'parmesan',
        'cheddar', 'brie', 'ghee', 'sour cream', 'ricotta', 'kefir',
    ],
    'Frozen': [
        'frozen', 'ice cream', 'freezer',
    ],
}


def _categorize_item(item_name):
    """Auto-categorize an item by keyword matching."""
    name_lower = item_name.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                return cat
    return 'Pantry'


def _match_meal(name):
    name_lower = name.lower().strip()
    if name in MEAL_INGREDIENTS:
        return MEAL_INGREDIENTS[name]
    for key, val in MEAL_INGREDIENTS.items():
        if key.lower() == name_lower:
            return val
    for key, val in MEAL_INGREDIENTS.items():
        key_words = set(key.lower().split())
        name_words = set(name_lower.split())
        overlap = key_words & name_words
        if len(overlap) >= 2:
            return val
    return None


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
        if abs((d - today).days) <= 6:
            for col in ('Breakfast', 'Lunch', 'Dinner', 'Snack'):
                val = str(row.get(col, '')).strip()
                if val and val.lower() not in ('', 'none', '-', 'n/a'):
                    meals.append(val)
    return list(dict.fromkeys(meals))


def _build_list(meal_names):
    all_ingredients = {}  # name → category
    unmatched_meals = []

    for meal in meal_names:
        ingr = _match_meal(meal)
        if ingr:
            for item, cat in ingr:
                item_lower = item.lower()
                if item_lower not in all_ingredients:
                    all_ingredients[item_lower] = (item, cat)
        else:
            unmatched_meals.append(meal)

    grouped = {'Produce': [], 'Protein': [], 'Dairy': [], 'Pantry': [], 'Frozen': [], 'Other': []}
    for _, (item, cat) in sorted(all_ingredients.items()):
        if cat not in grouped:
            cat = 'Other'
        grouped[cat].append({
            'name': item,
            'id': f"item_{item.lower().replace(' ', '_').replace('(', '').replace(')', '')}",
            'sprouts_url': _sprouts_url(item, cat),
            'wholefoods_url': _wf_url(item, cat),
            'organic': cat in ('Produce', 'Dairy'),
        })

    for cat in grouped:
        grouped[cat].sort(key=lambda x: x['name'].lower())

    if unmatched_meals:
        for meal in unmatched_meals:
            grouped['Other'].append({
                'name': meal,
                'id': f"item_meal_{meal.lower().replace(' ', '_')[:30]}",
                'sprouts_url': _sprouts_url(meal, 'Other'),
                'wholefoods_url': _wf_url(meal, 'Other'),
                'organic': False,
            })

    grouped = {k: v for k, v in grouped.items() if v}
    return grouped, unmatched_meals


def _sprouts_url(item, category):
    prefix = "organic " if category in ("Produce", "Dairy") else ""
    encoded = quote_plus(f"{prefix}{item}")
    return f"https://shop.sprouts.com/search?search_term={encoded}"


def _wf_url(item, category):
    prefix = "organic " if category in ("Produce", "Dairy") else ""
    encoded = quote_plus(f"{prefix}{item}")
    return f"https://www.wholefoodsmarket.com/search?text={encoded}"


@shopping_bp.route('/shopping')
@login_required
def index():
    meal_names = _this_weeks_meals()
    groups, unmatched = _build_list(meal_names)
    checked = session.get('checked_items', [])
    manual_items = session.get('manual_items', [])

    # Add manual items to groups
    for item_data in manual_items:
        name = item_data.get('name', '')
        cat = item_data.get('category', _categorize_item(name))
        if cat not in groups:
            groups[cat] = []
        groups[cat].append({
            'name': name,
            'id': item_data.get('id', f"manual_{name[:20]}"),
            'sprouts_url': _sprouts_url(name, cat),
            'wholefoods_url': _wf_url(name, cat),
            'organic': False,
            'manual': True,
        })

    # Count total items
    total_items = sum(len(v) for v in groups.values())

    return render_template(
        'shopping.html',
        groups=groups,
        meal_names=meal_names,
        unmatched=unmatched,
        checked=checked,
        total_items=total_items,
    )


@shopping_bp.route('/shopping/add', methods=['POST'])
@login_required
def add_item():
    """Add a manual item to the shopping list."""
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'No item name provided'}), 400

    manual_items = session.get('manual_items', [])
    category = _categorize_item(name)
    item_id = f"manual_{len(manual_items)}_{name[:20].replace(' ', '_')}"

    manual_items.append({
        'name': name,
        'category': category,
        'id': item_id,
    })
    session['manual_items'] = manual_items
    session.modified = True

    return jsonify({
        'success': True,
        'item': {
            'name': name,
            'category': category,
            'id': item_id,
            'sprouts_url': _sprouts_url(name, category),
            'wholefoods_url': _wf_url(name, category),
            'organic': False,
            'manual': True,
        },
        'total_items': sum(1 for _ in manual_items) + 1,
    })


@shopping_bp.route('/shopping/check', methods=['POST'])
@login_required
def check_item():
    """Toggle checked state for an item."""
    data = request.get_json()
    item_id = data.get('item_id', '')
    checked = session.get('checked_items', [])
    if item_id in checked:
        checked.remove(item_id)
        is_checked = False
    else:
        checked.append(item_id)
        is_checked = True
    session['checked_items'] = checked
    session.modified = True
    return jsonify({'success': True, 'checked': is_checked})


@shopping_bp.route('/shopping/clear-checked', methods=['POST'])
@login_required
def clear_checked():
    """Remove all checked items from manual list and clear checked state."""
    checked = session.get('checked_items', [])
    manual_items = session.get('manual_items', [])
    # Remove manual items that are checked
    manual_items = [i for i in manual_items if i.get('id') not in checked]
    session['manual_items'] = manual_items
    session['checked_items'] = []
    session.modified = True
    return jsonify({'success': True})


@shopping_bp.route('/shopping/item-count')
@login_required
def item_count():
    """Return current item count for badge."""
    meal_names = _this_weeks_meals()
    groups, _ = _build_list(meal_names)
    manual_items = session.get('manual_items', [])
    total = sum(len(v) for v in groups.values()) + len(manual_items)
    return jsonify({'count': total})


# ─────────────────────────────────────────────
# Shopping Intelligence — LLM ingredient suggestions
# ─────────────────────────────────────────────

def _load_llm_cache():
    if os.path.exists(_LLM_CACHE_PATH):
        try:
            with open(_LLM_CACHE_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_llm_cache(cache):
    try:
        with open(_LLM_CACHE_PATH, 'w') as f:
            json.dump(cache, f, indent=2)
    except OSError:
        pass


def _llm_suggest_ingredients(meal_name):
    """Call local LLM to generate ingredients for a meal name."""
    prompt = (
        f'List the grocery ingredients needed to make "{meal_name}". '
        'Respond ONLY with a JSON array (no explanation, no markdown). '
        'Each element must be an object with keys "name" (string) and '
        '"category" (one of: Produce, Protein, Dairy, Pantry). '
        'Example: [{"name": "chicken breast", "category": "Protein"}, ...]'
    )
    payload = {
        'model': _LLM_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.2,
        'max_tokens': 512,
    }
    resp = http_requests.post(
        f'{_LLM_BASE_URL}/chat/completions',
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    content = resp.json()['choices'][0]['message']['content'].strip()
    # Strip markdown code fences if present
    if content.startswith('```'):
        content = re.sub(r'^```[a-z]*\n?', '', content)
        content = re.sub(r'\n?```$', '', content)
    return json.loads(content)


@shopping_bp.route('/api/shopping/suggest', methods=['POST'])
@login_required
def suggest_ingredients():
    """
    POST /api/shopping/suggest
    Body: {"meal_name": "...", "force": false}
    Returns: {"ingredients": [...], "source": "static|llm"}
    """
    data = request.get_json(silent=True) or {}
    meal_name = str(data.get('meal_name', '')).strip()
    force = bool(data.get('force', False))

    if not meal_name:
        return jsonify({'error': 'meal_name is required'}), 400

    # 1. Check static MEAL_INGREDIENTS first (unless force=true)
    if not force:
        static = _match_meal(meal_name)
        if static:
            ingredients = [{'name': name, 'category': cat} for name, cat in static]
            return jsonify({'ingredients': ingredients, 'source': 'static'})

    # 2. Check LLM cache
    cache = _load_llm_cache()
    cache_key = meal_name.lower()
    if not force and cache_key in cache:
        return jsonify({'ingredients': cache[cache_key], 'source': 'llm'})

    # 3. Call LLM
    try:
        ingredients = _llm_suggest_ingredients(meal_name)
        if not isinstance(ingredients, list):
            raise ValueError('LLM did not return a list')
        # Normalise — ensure each item has name + category
        valid_cats = {'Produce', 'Protein', 'Dairy', 'Pantry'}
        normalised = []
        for item in ingredients:
            if isinstance(item, dict) and 'name' in item:
                cat = item.get('category', 'Pantry')
                if cat not in valid_cats:
                    cat = 'Pantry'
                normalised.append({'name': item['name'], 'category': cat})
        # Cache and return
        cache[cache_key] = normalised
        _save_llm_cache(cache)
        return jsonify({'ingredients': normalised, 'source': 'llm'})
    except Exception as exc:
        return jsonify({'error': f'LLM request failed: {exc}', 'ingredients': [], 'source': 'llm'}), 502
