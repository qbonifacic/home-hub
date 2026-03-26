from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.meal import Recipe
from backend.schemas.meal import RecipeCreate, RecipeUpdate


class RecipeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(
        self,
        search: str | None = None,
        tag: str | None = None,
        favorites_only: bool = False,
    ) -> list[Recipe]:
        query = select(Recipe).order_by(Recipe.name.asc())

        if search:
            query = query.where(
                or_(
                    Recipe.name.ilike(f"%{search}%"),
                    Recipe.description.ilike(f"%{search}%"),
                )
            )

        if tag:
            query = query.where(Recipe.tags.any(tag))

        if favorites_only:
            query = query.where(Recipe.is_favorite == True)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, recipe_id: int) -> Recipe:
        recipe = await self.db.get(Recipe, recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return recipe

    async def create(self, data: RecipeCreate) -> Recipe:
        recipe = Recipe(
            name=data.name,
            description=data.description,
            ingredients=[i.model_dump() for i in data.ingredients] if data.ingredients else [],
            instructions=data.instructions,
            prep_time_min=data.prep_time_min,
            cook_time_min=data.cook_time_min,
            servings=data.servings,
            nutritional_info=data.nutritional_info,
            tags=data.tags or [],
            image_url=data.image_url,
            is_favorite=data.is_favorite,
            source=data.source,
        )
        self.db.add(recipe)
        await self.db.commit()
        await self.db.refresh(recipe)
        return recipe

    async def update(self, recipe_id: int, data: RecipeUpdate) -> Recipe:
        recipe = await self.get(recipe_id)
        update_data = data.model_dump(exclude_unset=True)

        if "ingredients" in update_data and update_data["ingredients"] is not None:
            update_data["ingredients"] = [
                i.model_dump() if hasattr(i, "model_dump") else i
                for i in update_data["ingredients"]
            ]

        for key, value in update_data.items():
            setattr(recipe, key, value)

        await self.db.commit()
        await self.db.refresh(recipe)
        return recipe

    async def delete(self, recipe_id: int) -> dict:
        recipe = await self.get(recipe_id)
        await self.db.delete(recipe)
        await self.db.commit()
        return {"ok": True}

    async def toggle_favorite(self, recipe_id: int) -> Recipe:
        recipe = await self.get(recipe_id)
        recipe.is_favorite = not recipe.is_favorite
        await self.db.commit()
        await self.db.refresh(recipe)
        return recipe
