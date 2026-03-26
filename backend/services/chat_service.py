"""
Chat service using Claude's tool_use API to drive actions across all Home Hub modules.
"""

import json
import logging
from datetime import date, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.user import User
from backend.services.chore_service import ChoreService
from backend.services.meal_service import MealService
from backend.services.recipe_service import RecipeService
from backend.services.grocery_service import GroceryService
from backend.services.pantry_service import PantryService
from backend.services.outdoor_service import OutdoorService
from backend.services.home_service import HomeService
from backend.schemas.chore import ChoreCreate
from backend.schemas.meal import MealPlanCreate
from backend.schemas.pantry import PantryItemCreate
from backend.schemas.outdoor import OutdoorSessionCreate
from backend.schemas.grocery import GroceryItemCreate

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Home Hub assistant for the Bonifacic family. You help manage their household by using the available tools.

Today's date is {today}.

Guidelines:
- Be concise and friendly. Use short responses.
- When the user asks a question, use the appropriate tool to get data, then answer naturally.
- When the user asks you to do something, use the tool and confirm what you did.
- For meal planning, the family has two adults and kids. Prefer practical, family-friendly meals unless told otherwise.
- When referring to dates, use natural language ("this Monday", "tomorrow") rather than raw dates.
- If a tool returns an error, explain it simply and suggest what the user can try.
- You can chain multiple tools in one turn if needed (e.g., generate a meal plan then generate a grocery list).
- For "this week", use the Monday of the current week as the start date.
"""

# ── Tool definitions for Claude API ─────────────────────────────

TOOLS = [
    {
        "name": "list_chores",
        "description": "List household chores. Can filter by status (overdue, due_today, upcoming) and/or who they're assigned to.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["overdue", "due_today", "upcoming"],
                    "description": "Filter by status. Omit to get all active chores.",
                },
                "assigned_to": {
                    "type": "string",
                    "description": "Filter by person (e.g. 'dj', 'wife')",
                },
            },
        },
    },
    {
        "name": "complete_chore",
        "description": "Mark a chore as completed by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chore_id": {"type": "integer", "description": "The chore ID to complete"},
                "notes": {"type": "string", "description": "Optional completion notes"},
            },
            "required": ["chore_id"],
        },
    },
    {
        "name": "create_chore",
        "description": "Create a new household chore.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Chore name"},
                "description": {"type": "string", "description": "Optional details"},
                "frequency": {
                    "type": "string",
                    "enum": ["daily", "weekly", "biweekly", "monthly", "quarterly", "one_time"],
                    "description": "How often the chore repeats",
                },
                "assigned_to": {"type": "string", "description": "Who is responsible (dj or wife)"},
            },
            "required": ["title", "frequency"],
        },
    },
    {
        "name": "get_meals",
        "description": "Get the meal plan for a week. Returns all breakfast, lunch, and dinner entries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "week_of": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format. Defaults to Monday of current week.",
                },
            },
        },
    },
    {
        "name": "generate_meal_plan",
        "description": "Generate a meal plan using AI. Can specify dietary preferences like 'keto', 'vegetarian', 'kid-friendly', etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date YYYY-MM-DD. Defaults to Monday of current week.",
                },
                "preferences": {
                    "type": "string",
                    "description": "Dietary preferences (e.g. 'keto', 'vegetarian', 'quick meals', 'kid-friendly')",
                },
                "num_days": {"type": "integer", "description": "Number of days (default 7)"},
                "meal_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Which meals to plan (default: breakfast, lunch, dinner)",
                },
            },
        },
    },
    {
        "name": "create_meal",
        "description": "Add a single meal to the plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_date": {"type": "string", "description": "Date YYYY-MM-DD"},
                "meal_type": {
                    "type": "string",
                    "enum": ["breakfast", "lunch", "dinner", "snack"],
                },
                "meal_name": {"type": "string", "description": "Name of the meal"},
            },
            "required": ["plan_date", "meal_type", "meal_name"],
        },
    },
    {
        "name": "search_recipes",
        "description": "Search saved recipes by name or tag.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Search term for recipe name"},
                "tag": {"type": "string", "description": "Filter by tag"},
                "favorites_only": {"type": "boolean", "description": "Only show favorites"},
            },
        },
    },
    {
        "name": "get_grocery_lists",
        "description": "Get all grocery lists, optionally filtered by status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "completed"],
                    "description": "Filter by list status",
                },
            },
        },
    },
    {
        "name": "generate_grocery_list",
        "description": "Auto-generate a grocery list from the week's meal plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "week_of": {
                    "type": "string",
                    "description": "Week start date YYYY-MM-DD. Defaults to Monday of current week.",
                },
            },
        },
    },
    {
        "name": "list_pantry",
        "description": "List pantry inventory items, optionally filtered by storage location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "enum": ["Pantry", "Fridge", "Freezer"],
                    "description": "Filter by storage location",
                },
            },
        },
    },
    {
        "name": "add_pantry_item",
        "description": "Add an item to the pantry inventory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "Item name"},
                "quantity": {"type": "string", "description": "Amount (e.g. '2 lbs', '1 bag')"},
                "storage_location": {
                    "type": "string",
                    "enum": ["Pantry", "Fridge", "Freezer"],
                    "description": "Where to store it (default: Pantry)",
                },
                "expiration_date": {
                    "type": "string",
                    "description": "Expiration date YYYY-MM-DD if known",
                },
                "category": {"type": "string", "description": "Category (e.g. 'Produce', 'Dairy')"},
            },
            "required": ["item_name"],
        },
    },
    {
        "name": "mark_pantry_consumed",
        "description": "Mark a pantry item as consumed/used up.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "integer", "description": "The pantry item ID"},
            },
            "required": ["item_id"],
        },
    },
    {
        "name": "get_expiring_pantry",
        "description": "Get pantry items that are expiring soon.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Look ahead N days (default 7)",
                },
            },
        },
    },
    {
        "name": "get_outdoor_stats",
        "description": "Get outdoor time statistics for the kids. Can filter by date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
            },
        },
    },
    {
        "name": "log_outdoor_session",
        "description": "Log an outdoor play session for the kids.",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_date": {"type": "string", "description": "Date YYYY-MM-DD (default today)"},
                "start_time": {"type": "string", "description": "Start time HH:MM"},
                "end_time": {"type": "string", "description": "End time HH:MM"},
                "location": {"type": "string", "description": "Where they played"},
                "activity": {"type": "string", "description": "What they did"},
                "weather": {"type": "string", "description": "Weather conditions"},
                "notes": {"type": "string", "description": "Optional notes"},
            },
            "required": ["start_time", "end_time", "location"],
        },
    },
    {
        "name": "list_maintenance_tasks",
        "description": "List home maintenance tasks, optionally for a specific appliance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "appliance_id": {"type": "integer", "description": "Filter by appliance ID"},
            },
        },
    },
    {
        "name": "complete_maintenance_task",
        "description": "Mark a maintenance task as completed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "The task ID to complete"},
                "notes": {"type": "string", "description": "Completion notes"},
                "cost": {"type": "number", "description": "Cost if applicable"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "list_appliances",
        "description": "List registered home appliances.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by category (e.g. 'HVAC', 'Kitchen')"},
            },
        },
    },
]


def _monday_of_week() -> date:
    """Get Monday of the current week."""
    today = date.today()
    return today - timedelta(days=today.weekday())


def _serialize(obj) -> str:
    """JSON-serialize an ORM object or dict for Claude tool results."""
    if isinstance(obj, dict):
        return json.dumps(obj, default=str)
    if isinstance(obj, list):
        items = []
        for item in obj:
            if hasattr(item, "__dict__"):
                d = {k: v for k, v in item.__dict__.items() if not k.startswith("_")}
                items.append(d)
            else:
                items.append(item)
        return json.dumps(items, default=str)
    if hasattr(obj, "__dict__"):
        d = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        return json.dumps(d, default=str)
    return str(obj)


class ChatService:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.chores = ChoreService(db)
        self.meals = MealService(db)
        self.recipes = RecipeService(db)
        self.grocery = GroceryService(db)
        self.pantry = PantryService(db)
        self.outdoor = OutdoorService(db)
        self.home = HomeService(db)
        self.actions_taken: list[dict] = []

    async def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result as a string for Claude."""
        try:
            result = await self._dispatch_tool(tool_name, tool_input)
            return _serialize(result)
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return json.dumps({"error": str(e)})

    async def _dispatch_tool(self, name: str, inp: dict):
        """Route tool call to the appropriate service method."""

        if name == "list_chores":
            result = await self.chores.list_all(
                status=inp.get("status"),
                assigned_to=inp.get("assigned_to"),
            )
            self.actions_taken.append({"tool": name, "summary": f"Listed {len(result)} chores"})
            return result

        elif name == "complete_chore":
            result = await self.chores.mark_complete(
                chore_id=inp["chore_id"],
                user=self.user,
                notes=inp.get("notes"),
                source="chat",
            )
            self.actions_taken.append({"tool": name, "summary": f"Completed chore #{inp['chore_id']}"})
            return result

        elif name == "create_chore":
            data = ChoreCreate(
                title=inp["title"],
                description=inp.get("description"),
                frequency=inp["frequency"],
                assigned_to=inp.get("assigned_to"),
            )
            result = await self.chores.create(data, self.user)
            self.actions_taken.append({"tool": name, "summary": f"Created chore: {inp['title']}"})
            return result

        elif name == "get_meals":
            week_of_str = inp.get("week_of")
            week_of = date.fromisoformat(week_of_str) if week_of_str else _monday_of_week()
            result = await self.meals.get_week(week_of)
            total = sum(len(v) for v in result.values())
            self.actions_taken.append({"tool": name, "summary": f"Retrieved {total} meals for the week"})
            return result

        elif name == "generate_meal_plan":
            start_str = inp.get("start_date")
            start_date = date.fromisoformat(start_str) if start_str else _monday_of_week()
            result = await self.meals.generate_with_ai(
                start_date=start_date,
                user=self.user,
                preferences=inp.get("preferences"),
                num_days=inp.get("num_days", 7),
                meal_types=inp.get("meal_types"),
            )
            self.actions_taken.append({"tool": name, "summary": f"Generated {len(result)} meals"})
            return result

        elif name == "create_meal":
            data = MealPlanCreate(
                plan_date=date.fromisoformat(inp["plan_date"]),
                meal_type=inp["meal_type"],
                meal_name=inp["meal_name"],
                source="chat",
            )
            result = await self.meals.create(data, self.user)
            self.actions_taken.append({"tool": name, "summary": f"Added meal: {inp['meal_name']}"})
            return result

        elif name == "search_recipes":
            result = await self.recipes.list_all(
                search=inp.get("search"),
                tag=inp.get("tag"),
                favorites_only=inp.get("favorites_only", False),
            )
            self.actions_taken.append({"tool": name, "summary": f"Found {len(result)} recipes"})
            return result

        elif name == "get_grocery_lists":
            result = await self.grocery.list_all(status=inp.get("status"))
            self.actions_taken.append({"tool": name, "summary": f"Found {len(result)} grocery lists"})
            return result

        elif name == "generate_grocery_list":
            week_of_str = inp.get("week_of")
            week_of = date.fromisoformat(week_of_str) if week_of_str else _monday_of_week()
            result = await self.grocery.generate_from_meals(week_of, self.user)
            self.actions_taken.append({"tool": name, "summary": "Generated grocery list from meal plan"})
            return result

        elif name == "list_pantry":
            result = await self.pantry.list_all(location=inp.get("location"))
            self.actions_taken.append({"tool": name, "summary": f"Listed {len(result)} pantry items"})
            return result

        elif name == "add_pantry_item":
            exp_date = None
            if inp.get("expiration_date"):
                exp_date = date.fromisoformat(inp["expiration_date"])
            data = PantryItemCreate(
                item_name=inp["item_name"],
                quantity=inp.get("quantity"),
                storage_location=inp.get("storage_location", "Pantry"),
                expiration_date=exp_date,
                category=inp.get("category"),
            )
            result = await self.pantry.create(data)
            self.actions_taken.append({"tool": name, "summary": f"Added to pantry: {inp['item_name']}"})
            return result

        elif name == "mark_pantry_consumed":
            result = await self.pantry.mark_consumed(inp["item_id"])
            self.actions_taken.append({"tool": name, "summary": f"Marked pantry item #{inp['item_id']} as consumed"})
            return result

        elif name == "get_expiring_pantry":
            result = await self.pantry.get_expiring(days_ahead=inp.get("days_ahead", 7))
            self.actions_taken.append({"tool": name, "summary": f"Found {len(result)} expiring items"})
            return result

        elif name == "get_outdoor_stats":
            start = date.fromisoformat(inp["start_date"]) if inp.get("start_date") else None
            end = date.fromisoformat(inp["end_date"]) if inp.get("end_date") else None
            result = await self.outdoor.get_stats(start_date=start, end_date=end)
            self.actions_taken.append({"tool": name, "summary": "Retrieved outdoor stats"})
            return result

        elif name == "log_outdoor_session":
            data = OutdoorSessionCreate(
                session_date=date.fromisoformat(inp.get("session_date", str(date.today()))),
                start_time=inp["start_time"],
                end_time=inp["end_time"],
                location=inp["location"],
                activity=inp.get("activity"),
                weather=inp.get("weather"),
                notes=inp.get("notes"),
                source="chat",
            )
            result = await self.outdoor.create(data, self.user)
            self.actions_taken.append({"tool": name, "summary": f"Logged outdoor session at {inp['location']}"})
            return result

        elif name == "list_maintenance_tasks":
            result = await self.home.list_tasks(appliance_id=inp.get("appliance_id"))
            self.actions_taken.append({"tool": name, "summary": f"Listed {len(result)} maintenance tasks"})
            return result

        elif name == "complete_maintenance_task":
            result = await self.home.complete_task(
                task_id=inp["task_id"],
                notes=inp.get("notes"),
                cost=inp.get("cost"),
            )
            self.actions_taken.append({"tool": name, "summary": f"Completed maintenance task #{inp['task_id']}"})
            return result

        elif name == "list_appliances":
            result = await self.home.list_appliances(category=inp.get("category"))
            self.actions_taken.append({"tool": name, "summary": f"Listed {len(result)} appliances"})
            return result

        else:
            return {"error": f"Unknown tool: {name}"}

    async def chat(self, message: str) -> dict:
        """
        Process a chat message using Claude's tool_use API.
        Returns {"response": str, "actions_taken": list}.
        """
        self.actions_taken = []

        system = SYSTEM_PROMPT.format(today=date.today().isoformat())

        messages = [{"role": "user", "content": message}]

        max_iterations = 10

        for iteration in range(max_iterations):
            async with httpx.AsyncClient(timeout=120.0) as client:
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
                        "system": system,
                        "tools": TOOLS,
                        "messages": messages,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            # Check stop reason
            stop_reason = data.get("stop_reason", "end_turn")

            if stop_reason == "end_turn":
                # Extract text response
                text_parts = []
                for block in data.get("content", []):
                    if block["type"] == "text":
                        text_parts.append(block["text"])

                return {
                    "response": "\n".join(text_parts) if text_parts else "Done!",
                    "actions_taken": self.actions_taken,
                }

            elif stop_reason == "tool_use":
                # Add assistant's response to conversation
                messages.append({"role": "assistant", "content": data["content"]})

                # Process all tool calls
                tool_results = []
                for block in data.get("content", []):
                    if block["type"] == "tool_use":
                        tool_name = block["name"]
                        tool_input = block["input"]
                        tool_id = block["id"]

                        logger.info(f"Chat executing tool: {tool_name}({tool_input})")
                        result_str = await self._execute_tool(tool_name, tool_input)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_str,
                        })

                # Add tool results to conversation
                messages.append({"role": "user", "content": tool_results})

            else:
                # Unexpected stop reason
                text_parts = []
                for block in data.get("content", []):
                    if block["type"] == "text":
                        text_parts.append(block["text"])
                return {
                    "response": "\n".join(text_parts) if text_parts else "Something unexpected happened.",
                    "actions_taken": self.actions_taken,
                }

        # Max iterations reached
        return {
            "response": "I've been working on this for a while. Let me know if you need anything else!",
            "actions_taken": self.actions_taken,
        }
