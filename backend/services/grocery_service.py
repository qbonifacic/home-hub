from datetime import date, datetime, timedelta, timezone
import json
import logging
from urllib.parse import quote_plus

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import httpx

from backend.config import settings
from backend.models.grocery import GroceryList, GroceryItem
from backend.models.meal import MealPlan
from backend.models.user import User
from backend.schemas.grocery import GroceryItemCreate, GroceryItemUpdate

logger = logging.getLogger(__name__)

# ── Category keywords for auto-categorization ────────────────
CATEGORY_KEYWORDS = {
    "Produce": [
        "apple", "banana", "orange", "lemon", "lime", "avocado", "tomato", "onion",
        "garlic", "potato", "lettuce", "spinach", "kale", "broccoli", "carrot",
        "celery", "pepper", "cucumber", "zucchini", "mushroom", "corn", "bean",
        "pea", "squash", "sweet potato", "cilantro", "parsley", "basil", "mint",
        "ginger", "jalapeño", "serrano", "poblano", "arugula", "cabbage", "berry",
        "strawberry", "blueberry", "raspberry", "grape", "mango", "pineapple",
        "peach", "pear", "melon", "watermelon", "cantaloupe", "asparagus",
    ],
    "Meat & Seafood": [
        "chicken", "beef", "pork", "salmon", "shrimp", "turkey", "sausage",
        "bacon", "ham", "steak", "ground beef", "ground turkey", "tilapia",
        "cod", "tuna", "lamb", "chorizo", "meatball", "ribs", "brisket",
    ],
    "Dairy & Eggs": [
        "milk", "cheese", "yogurt", "butter", "cream", "egg", "sour cream",
        "cream cheese", "mozzarella", "cheddar", "parmesan", "feta",
        "cottage cheese", "heavy cream", "half and half", "whipping cream",
    ],
    "Bakery & Bread": [
        "bread", "tortilla", "bun", "roll", "bagel", "pita", "naan",
        "croissant", "english muffin", "flatbread", "ciabatta",
    ],
    "Pantry": [
        "rice", "pasta", "flour", "sugar", "oil", "vinegar", "soy sauce",
        "broth", "stock", "can", "beans", "tomato sauce", "tomato paste",
        "coconut milk", "peanut butter", "jam", "honey", "maple syrup",
        "oat", "cereal", "granola", "chip", "cracker", "nut", "almond",
        "walnut", "pecan", "cashew", "dried", "lentil", "quinoa", "couscous",
    ],
    "Spices & Seasonings": [
        "salt", "pepper", "cumin", "paprika", "cinnamon", "oregano", "thyme",
        "rosemary", "turmeric", "chili powder", "cayenne", "nutmeg", "clove",
        "coriander", "bay leaf", "italian seasoning", "garlic powder",
        "onion powder", "red pepper flakes", "taco seasoning",
    ],
    "Frozen": [
        "frozen", "ice cream", "pizza", "waffle", "french fries", "tater tots",
        "frozen fruit", "popsicle", "frozen vegetable",
    ],
    "Beverages": [
        "water", "juice", "soda", "coffee", "tea", "kombucha", "sparkling",
        "lemonade", "smoothie",
    ],
    "Snacks": [
        "granola bar", "fruit snack", "popcorn", "pretzel", "trail mix",
        "dried fruit", "fruit leather", "goldfish", "animal cracker",
    ],
}

# ── Known meal → ingredient mappings (ported from old app) ──
MEAL_INGREDIENTS: dict[str, list[dict]] = {
    "tacos": [
        {"name": "ground beef", "quantity": "1", "unit": "lb", "category": "Meat & Seafood"},
        {"name": "taco shells", "quantity": "1", "unit": "box", "category": "Pantry"},
        {"name": "cheddar cheese", "quantity": "1", "unit": "cup", "category": "Dairy & Eggs"},
        {"name": "lettuce", "quantity": "1", "unit": "head", "category": "Produce"},
        {"name": "tomato", "quantity": "2", "unit": "", "category": "Produce"},
        {"name": "sour cream", "quantity": "1", "unit": "container", "category": "Dairy & Eggs"},
        {"name": "taco seasoning", "quantity": "1", "unit": "packet", "category": "Spices & Seasonings"},
    ],
    "spaghetti": [
        {"name": "spaghetti pasta", "quantity": "1", "unit": "lb", "category": "Pantry"},
        {"name": "ground beef", "quantity": "1", "unit": "lb", "category": "Meat & Seafood"},
        {"name": "marinara sauce", "quantity": "1", "unit": "jar", "category": "Pantry"},
        {"name": "parmesan cheese", "quantity": "1", "unit": "cup", "category": "Dairy & Eggs"},
        {"name": "garlic bread", "quantity": "1", "unit": "loaf", "category": "Bakery & Bread"},
    ],
    "grilled chicken": [
        {"name": "chicken breast", "quantity": "2", "unit": "lbs", "category": "Meat & Seafood"},
        {"name": "olive oil", "quantity": "2", "unit": "tbsp", "category": "Pantry"},
        {"name": "garlic", "quantity": "3", "unit": "cloves", "category": "Produce"},
        {"name": "lemon", "quantity": "1", "unit": "", "category": "Produce"},
    ],
    "stir fry": [
        {"name": "chicken breast", "quantity": "1", "unit": "lb", "category": "Meat & Seafood"},
        {"name": "broccoli", "quantity": "2", "unit": "cups", "category": "Produce"},
        {"name": "bell pepper", "quantity": "2", "unit": "", "category": "Produce"},
        {"name": "soy sauce", "quantity": "3", "unit": "tbsp", "category": "Pantry"},
        {"name": "rice", "quantity": "2", "unit": "cups", "category": "Pantry"},
        {"name": "sesame oil", "quantity": "1", "unit": "tbsp", "category": "Pantry"},
        {"name": "ginger", "quantity": "1", "unit": "inch", "category": "Produce"},
    ],
    "pizza": [
        {"name": "pizza dough", "quantity": "1", "unit": "lb", "category": "Bakery & Bread"},
        {"name": "mozzarella cheese", "quantity": "2", "unit": "cups", "category": "Dairy & Eggs"},
        {"name": "pizza sauce", "quantity": "1", "unit": "cup", "category": "Pantry"},
        {"name": "pepperoni", "quantity": "1", "unit": "package", "category": "Meat & Seafood"},
    ],
    "salmon": [
        {"name": "salmon fillet", "quantity": "1.5", "unit": "lbs", "category": "Meat & Seafood"},
        {"name": "lemon", "quantity": "1", "unit": "", "category": "Produce"},
        {"name": "asparagus", "quantity": "1", "unit": "bunch", "category": "Produce"},
        {"name": "olive oil", "quantity": "2", "unit": "tbsp", "category": "Pantry"},
        {"name": "garlic", "quantity": "2", "unit": "cloves", "category": "Produce"},
    ],
    "burgers": [
        {"name": "ground beef", "quantity": "2", "unit": "lbs", "category": "Meat & Seafood"},
        {"name": "hamburger buns", "quantity": "1", "unit": "package", "category": "Bakery & Bread"},
        {"name": "cheddar cheese", "quantity": "4", "unit": "slices", "category": "Dairy & Eggs"},
        {"name": "lettuce", "quantity": "1", "unit": "head", "category": "Produce"},
        {"name": "tomato", "quantity": "2", "unit": "", "category": "Produce"},
        {"name": "onion", "quantity": "1", "unit": "", "category": "Produce"},
    ],
    "mac and cheese": [
        {"name": "elbow macaroni", "quantity": "1", "unit": "lb", "category": "Pantry"},
        {"name": "cheddar cheese", "quantity": "3", "unit": "cups", "category": "Dairy & Eggs"},
        {"name": "milk", "quantity": "2", "unit": "cups", "category": "Dairy & Eggs"},
        {"name": "butter", "quantity": "3", "unit": "tbsp", "category": "Dairy & Eggs"},
        {"name": "flour", "quantity": "2", "unit": "tbsp", "category": "Pantry"},
    ],
    "chicken soup": [
        {"name": "chicken breast", "quantity": "1", "unit": "lb", "category": "Meat & Seafood"},
        {"name": "chicken broth", "quantity": "2", "unit": "quarts", "category": "Pantry"},
        {"name": "carrots", "quantity": "3", "unit": "", "category": "Produce"},
        {"name": "celery", "quantity": "3", "unit": "stalks", "category": "Produce"},
        {"name": "egg noodles", "quantity": "2", "unit": "cups", "category": "Pantry"},
        {"name": "onion", "quantity": "1", "unit": "", "category": "Produce"},
    ],
    "quesadillas": [
        {"name": "flour tortillas", "quantity": "1", "unit": "package", "category": "Bakery & Bread"},
        {"name": "cheddar cheese", "quantity": "2", "unit": "cups", "category": "Dairy & Eggs"},
        {"name": "chicken breast", "quantity": "1", "unit": "lb", "category": "Meat & Seafood"},
        {"name": "salsa", "quantity": "1", "unit": "jar", "category": "Pantry"},
        {"name": "sour cream", "quantity": "1", "unit": "container", "category": "Dairy & Eggs"},
    ],
}


def _categorize_item(item_name: str) -> str:
    """Auto-categorize a grocery item by keyword matching."""
    name_lower = item_name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name_lower:
                return category
    return "Pantry"


def _sprouts_url(item_name: str) -> str:
    """Generate a Sprouts Farmers Market search URL."""
    return f"https://www.sprouts.com/search/?search_term={quote_plus(item_name)}"


def _wholefoods_url(item_name: str) -> str:
    """Generate a Whole Foods search URL."""
    return f"https://www.wholefoodsmarket.com/search?text={quote_plus(item_name)}"


def _match_meal(meal_name: str) -> list[dict] | None:
    """Match a meal name to known ingredient lists."""
    name_lower = meal_name.lower().strip()
    # Exact match first
    if name_lower in MEAL_INGREDIENTS:
        return MEAL_INGREDIENTS[name_lower]
    # Partial match
    for key, ingredients in MEAL_INGREDIENTS.items():
        if key in name_lower or name_lower in key:
            return ingredients
    return None


class GroceryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, status: str | None = None) -> list[GroceryList]:
        query = select(GroceryList).order_by(GroceryList.week_of.desc())
        if status:
            query = query.where(GroceryList.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, list_id: int) -> GroceryList:
        grocery_list = await self.db.get(GroceryList, list_id)
        if not grocery_list:
            raise HTTPException(status_code=404, detail="Grocery list not found")
        return grocery_list

    async def get_items(self, list_id: int) -> list[GroceryItem]:
        result = await self.db.execute(
            select(GroceryItem)
            .where(GroceryItem.list_id == list_id)
            .order_by(GroceryItem.category.asc(), GroceryItem.item_name.asc())
        )
        return list(result.scalars().all())

    async def create_list(self, week_of: date, name: str | None = None) -> GroceryList:
        grocery_list = GroceryList(
            week_of=week_of,
            name=name or f"Week of {week_of.strftime('%b %d')}",
            status="active",
        )
        self.db.add(grocery_list)
        await self.db.commit()
        await self.db.refresh(grocery_list)
        return grocery_list

    async def add_item(self, list_id: int, data: GroceryItemCreate) -> GroceryItem:
        # Ensure list exists
        await self.get(list_id)

        category = data.category if data.category != "Pantry" else _categorize_item(data.item_name)
        item = GroceryItem(
            list_id=list_id,
            item_name=data.item_name,
            category=category,
            quantity=data.quantity,
            is_manual=data.is_manual,
            notes=data.notes,
            sprouts_url=_sprouts_url(data.item_name),
            wholefoods_url=_wholefoods_url(data.item_name),
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_item(self, item_id: int, data: GroceryItemUpdate, user: User | None = None) -> GroceryItem:
        item = await self.db.get(GroceryItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Grocery item not found")

        update_data = data.model_dump(exclude_unset=True)

        if "is_purchased" in update_data and update_data["is_purchased"]:
            item.purchased_at = datetime.now(timezone.utc)
            item.purchased_by = user.username if user else None

        for key, value in update_data.items():
            setattr(item, key, value)

        # Regenerate store URLs if name changed
        if "item_name" in update_data:
            item.sprouts_url = _sprouts_url(item.item_name)
            item.wholefoods_url = _wholefoods_url(item.item_name)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_item(self, item_id: int) -> dict:
        item = await self.db.get(GroceryItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Grocery item not found")
        await self.db.delete(item)
        await self.db.commit()
        return {"ok": True}

    async def update_list_status(self, list_id: int, status: str) -> GroceryList:
        grocery_list = await self.get(list_id)
        grocery_list.status = status
        await self.db.commit()
        await self.db.refresh(grocery_list)
        return grocery_list

    async def generate_from_meals(self, week_of: date, user: User, list_name: str | None = None) -> GroceryList:
        """Generate a grocery list from the week's meal plans."""
        # Get all meals for the week
        end_date = week_of + timedelta(days=6)
        result = await self.db.execute(
            select(MealPlan).where(
                and_(MealPlan.plan_date >= week_of, MealPlan.plan_date <= end_date)
            )
        )
        meals = list(result.scalars().all())

        if not meals:
            raise HTTPException(status_code=400, detail="No meals planned for this week")

        # Create the grocery list
        grocery_list = await self.create_list(week_of, list_name)

        # Collect all ingredients, deduplicating
        ingredients_map: dict[str, dict] = {}
        unmatched_meals: list[str] = []

        for meal in meals:
            matched = _match_meal(meal.meal_name)
            if matched:
                for ing in matched:
                    key = ing["name"].lower()
                    if key not in ingredients_map:
                        ingredients_map[key] = ing
            else:
                unmatched_meals.append(meal.meal_name)

        # For unmatched meals, try Ollama for ingredient suggestions
        if unmatched_meals:
            ollama_ingredients = await self._get_ingredients_from_ollama(unmatched_meals)
            for ing in ollama_ingredients:
                key = ing["name"].lower()
                if key not in ingredients_map:
                    ingredients_map[key] = ing

        # Add all ingredients to the list
        for ing in ingredients_map.values():
            category = ing.get("category") or _categorize_item(ing["name"])
            item = GroceryItem(
                list_id=grocery_list.id,
                item_name=ing["name"],
                category=category,
                quantity=ing.get("quantity", ""),
                sprouts_url=_sprouts_url(ing["name"]),
                wholefoods_url=_wholefoods_url(ing["name"]),
            )
            self.db.add(item)

        await self.db.commit()
        await self.db.refresh(grocery_list)
        return grocery_list

    async def _get_ingredients_from_ollama(self, meal_names: list[str]) -> list[dict]:
        """Use local Ollama to suggest ingredients for unmatched meals."""
        try:
            meals_text = ", ".join(meal_names)
            prompt = f"""For these meals: {meals_text}

List the grocery ingredients needed. Return ONLY a JSON array like:
[{{"name": "chicken breast", "quantity": "2 lbs", "category": "Meat & Seafood"}}]

Categories: Produce, Meat & Seafood, Dairy & Eggs, Bakery & Bread, Pantry, Spices & Seasonings, Frozen, Beverages
Only include items that need to be purchased, not basic pantry staples like salt/pepper/oil.
Return ONLY the JSON array."""

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": "llama3.3:70b",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3},
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            response_text = data.get("response", "")
            # Extract JSON
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            # Find the JSON array
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(response_text[start:end])

        except Exception as e:
            logger.warning(f"Ollama ingredient suggestion failed: {e}")

        return []
