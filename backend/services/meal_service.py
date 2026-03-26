from datetime import date, timedelta
import json
import logging

from fastapi import HTTPException
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from backend.config import settings
from backend.models.meal import MealPlan
from backend.models.user import User
from backend.schemas.meal import MealPlanCreate, MealPlanUpdate

logger = logging.getLogger(__name__)


class MealService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_week(self, week_of: date) -> dict[str, list[MealPlan]]:
        """Get all meals for a 7-day period starting from week_of."""
        end_date = week_of + timedelta(days=6)
        result = await self.db.execute(
            select(MealPlan)
            .where(and_(MealPlan.plan_date >= week_of, MealPlan.plan_date <= end_date))
            .order_by(MealPlan.plan_date.asc(), MealPlan.meal_type.asc())
        )
        meals = list(result.scalars().all())

        # Group by date
        days: dict[str, list[MealPlan]] = {}
        for d in range(7):
            day = week_of + timedelta(days=d)
            day_str = day.isoformat()
            days[day_str] = [m for m in meals if m.plan_date == day]

        return days

    async def get_today(self) -> list[MealPlan]:
        """Get meals for today."""
        result = await self.db.execute(
            select(MealPlan)
            .where(MealPlan.plan_date == date.today())
            .order_by(MealPlan.meal_type.asc())
        )
        return list(result.scalars().all())

    async def create(self, data: MealPlanCreate, user: User) -> MealPlan:
        meal = MealPlan(
            plan_date=data.plan_date,
            meal_type=data.meal_type,
            meal_name=data.meal_name,
            recipe_id=data.recipe_id,
            notes=data.notes,
            created_by=user.username,
            source=data.source,
        )
        self.db.add(meal)
        await self.db.commit()
        await self.db.refresh(meal)
        return meal

    async def update(self, meal_id: int, data: MealPlanUpdate) -> MealPlan:
        meal = await self.db.get(MealPlan, meal_id)
        if not meal:
            raise HTTPException(status_code=404, detail="Meal plan entry not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(meal, key, value)

        await self.db.commit()
        await self.db.refresh(meal)
        return meal

    async def delete(self, meal_id: int) -> dict:
        meal = await self.db.get(MealPlan, meal_id)
        if not meal:
            raise HTTPException(status_code=404, detail="Meal plan entry not found")
        await self.db.delete(meal)
        await self.db.commit()
        return {"ok": True}

    async def generate_with_ai(
        self,
        start_date: date,
        user: User,
        preferences: str | None = None,
        num_days: int = 7,
        meal_types: list[str] | None = None,
    ) -> list[MealPlan]:
        """Use Claude Sonnet to generate a weekly meal plan."""
        if not settings.anthropic_api_key:
            raise HTTPException(status_code=503, detail="Anthropic API key not configured")

        meal_types = meal_types or ["breakfast", "lunch", "dinner"]
        pref_text = f"\nDietary preferences/constraints: {preferences}" if preferences else ""

        prompt = f"""Generate a {num_days}-day meal plan for a family.
Meal types needed: {', '.join(meal_types)}
Start date: {start_date.isoformat()}{pref_text}

IMPORTANT: Return ONLY a JSON array with objects like:
[
  {{"date": "2026-03-11", "meal_type": "breakfast", "meal_name": "Scrambled Eggs with Toast"}},
  {{"date": "2026-03-11", "meal_type": "lunch", "meal_name": "Chicken Caesar Salad"}},
  ...
]

Guidelines:
- Vary the meals, don't repeat within the same week
- Include a mix of easy and more involved meals
- Keep it practical for a family with kids
- Use real, specific meal names (not generic like "pasta dish")
- Return ONLY the JSON array, no other text"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 4096,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            # Parse the response
            content = data["content"][0]["text"]
            # Extract JSON if wrapped in markdown code blocks
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            meal_items = json.loads(content)

            # Clear existing meals for the date range
            end_date = start_date + timedelta(days=num_days - 1)
            await self.db.execute(
                delete(MealPlan).where(
                    and_(
                        MealPlan.plan_date >= start_date,
                        MealPlan.plan_date <= end_date,
                        MealPlan.source == "ai",
                    )
                )
            )

            # Create new meal plans
            created = []
            for item in meal_items:
                meal = MealPlan(
                    plan_date=date.fromisoformat(item["date"]),
                    meal_type=item["meal_type"],
                    meal_name=item["meal_name"],
                    created_by=user.username,
                    source="ai",
                )
                self.db.add(meal)
                created.append(meal)

            await self.db.commit()
            for meal in created:
                await self.db.refresh(meal)

            return created

        except httpx.HTTPError as e:
            logger.error(f"AI meal generation failed: {e}")
            raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise HTTPException(status_code=502, detail="Failed to parse AI-generated meal plan")
