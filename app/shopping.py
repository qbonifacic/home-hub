import re
from datetime import date
from urllib.parse import quote_plus

from flask import Blueprint, render_template
from flask_login import login_required

from .sheets import get_all_records

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

# Fuzzy-match a meal name to the database
def _match_meal(name):
    name_lower = name.lower().strip()
    # Exact match first
    if name in MEAL_INGREDIENTS:
        return MEAL_INGREDIENTS[name]
    # Case-insensitive
    for key, val in MEAL_INGREDIENTS.items():
        if key.lower() == name_lower:
            return val
    # Partial match — name contains a key word
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
    # Collect all ingredients across all meals this week
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

    # Group by category
    grouped = {'Produce': [], 'Protein': [], 'Dairy': [], 'Pantry': []}
    for _, (item, cat) in sorted(all_ingredients.items()):
        grouped[cat].append({
            'name': item,
            'sprouts_url': _sprouts_url(item, cat),
            'wholefoods_url': _wf_url(item, cat),
            'organic': cat in ('Produce', 'Dairy'),
        })

    # Sort each category alphabetically
    for cat in grouped:
        grouped[cat].sort(key=lambda x: x['name'].lower())

    # Remove empty categories
    grouped = {k: v for k, v in grouped.items() if v}
    return grouped, unmatched_meals


def _sprouts_url(item, category):
    """Build Sprouts search URL — organic prefix for Produce & Dairy."""
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
    return render_template('shopping.html', groups=groups, meal_names=meal_names, unmatched=unmatched)
