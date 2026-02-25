import os
import json
import datetime
import anthropic
import requests
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

chat_bp = Blueprint('chat', __name__)

SHEET_ID = '1pgFsQUT6_pK5I5dZU1S_eyqwDBBdndDd9LkB69MW6R0'


def get_anthropic_client():
    return anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))


def get_gc():
    """Get gspread client using service account credentials."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds_json = os.environ.get('GOOGLE_CREDS_JSON')
    if creds_json:
        info = json.loads(creds_json)
    else:
        with open('/Users/qbot/.openclaw/workspace/google_creds.json') as f:
            info = json.load(f)

    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)


def tool_get_meals():
    """Get this week's meal plan."""
    gc = get_gc()
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet('Weekly Meal Plan')
    records = ws.get_all_records()
    return json.dumps(records[:7])


def tool_update_meal(day_date: str, meal_type: str, new_value: str):
    """Update a specific meal. day_date format: M/D/YYYY e.g. 2/25/2026"""
    gc = get_gc()
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet('Weekly Meal Plan')
    records = ws.get_all_records()
    headers = ws.row_values(1)

    for i, row in enumerate(records):
        date_val = str(row.get('Date', ''))
        if day_date in date_val:
            col_idx = headers.index(meal_type) + 1
            ws.update_cell(i + 2, col_idx, new_value)
            return f"Updated {meal_type} on {day_date} to: {new_value}"
    return f"Could not find date {day_date} in meal plan"


def tool_get_chores():
    """Get all chores with their status."""
    gc = get_gc()
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet('Chores')
    return json.dumps(ws.get_all_records())


def tool_mark_chore_done(task_name: str):
    """Mark a chore as done today."""
    gc = get_gc()
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet('Chores')
    records = ws.get_all_records()
    headers = ws.row_values(1)
    today = datetime.date.today()

    for i, row in enumerate(records):
        if task_name.lower() in str(row.get('Task', '')).lower():
            # Update Last Done
            last_done_col = headers.index('Last Done') + 1
            ws.update_cell(i + 2, last_done_col, today.strftime('%-m/%-d/%Y'))

            # Calculate Next Due based on Frequency
            freq = str(row.get('Frequency', 'weekly')).lower()
            days = 7
            if 'daily' in freq:
                days = 1
            elif 'week' in freq:
                days = 7
            elif 'bi-week' in freq or 'biweek' in freq:
                days = 14
            elif 'month' in freq:
                days = 30

            next_due = today + datetime.timedelta(days=days)
            next_due_col = headers.index('Next Due') + 1
            ws.update_cell(i + 2, next_due_col, next_due.strftime('%-m/%-d/%Y'))
            return f"Marked '{row['Task']}' done. Next due: {next_due.strftime('%b %d')}"

    return f"Could not find chore: {task_name}"


def tool_add_reminder(title: str, due_date: str, notes: str = ''):
    """Add a reminder to the Reminders sheet."""
    gc = get_gc()
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet('Reminders')
    ws.append_row([title, due_date, notes, 'Pending'])
    return f"Added reminder: {title} due {due_date}"


def tool_get_weather():
    """Get current Fort Collins weather."""
    r = requests.get(
        'https://api.open-meteo.com/v1/forecast'
        '?latitude=40.5853&longitude=-105.0844'
        '&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m'
        '&temperature_unit=fahrenheit&wind_speed_unit=mph&forecast_days=1',
        timeout=8,
    )
    cur = r.json().get('current', {})
    return (
        f"{round(cur.get('temperature_2m', 0))}\u00b0F, "
        f"feels like {round(cur.get('apparent_temperature', 0))}\u00b0F, "
        f"{cur.get('relative_humidity_2m', 0)}% humidity, "
        f"{round(cur.get('wind_speed_10m', 0))} mph wind"
    )


TOOLS = [
    {"name": "get_meals", "description": "Get this week's meal plan from Google Sheets",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "update_meal", "description": "Update a specific meal in the meal plan",
     "input_schema": {"type": "object", "properties": {
         "day_date": {"type": "string", "description": "Date in M/D/YYYY format"},
         "meal_type": {"type": "string", "enum": ["Breakfast", "Lunch", "Dinner", "Snack"]},
         "new_value": {"type": "string"}},
         "required": ["day_date", "meal_type", "new_value"]}},
    {"name": "get_chores", "description": "Get all household chores and their status",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "mark_chore_done", "description": "Mark a chore as completed today",
     "input_schema": {"type": "object", "properties": {
         "task_name": {"type": "string"}},
         "required": ["task_name"]}},
    {"name": "add_reminder", "description": "Add a reminder",
     "input_schema": {"type": "object", "properties": {
         "title": {"type": "string"},
         "due_date": {"type": "string"},
         "notes": {"type": "string"}},
         "required": ["title", "due_date"]}},
    {"name": "get_weather", "description": "Get current Fort Collins weather",
     "input_schema": {"type": "object", "properties": {}}},
]

TOOL_FNS = {
    "get_meals": lambda inp: tool_get_meals(),
    "update_meal": lambda inp: tool_update_meal(inp['day_date'], inp['meal_type'], inp['new_value']),
    "get_chores": lambda inp: tool_get_chores(),
    "mark_chore_done": lambda inp: tool_mark_chore_done(inp['task_name']),
    "add_reminder": lambda inp: tool_add_reminder(inp['title'], inp['due_date'], inp.get('notes', '')),
    "get_weather": lambda inp: tool_get_weather(),
}


@chat_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'No message'}), 400

    client = get_anthropic_client()
    today = datetime.date.today().strftime('%A, %B %d, %Y')

    system = (
        f"You are Q, an AI butler for the Bonifacic household. Today is {today}. "
        "You help DJ and Angela manage their home \u2014 meals, chores, reminders, and more. "
        "When asked to make a change (update a meal, mark a chore done, add a reminder), USE THE TOOLS to actually do it. "
        "Keep responses brief and direct. No fluff."
    )

    messages = [{"role": "user", "content": user_message}]

    # Agentic loop
    for _ in range(5):
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == 'end_turn':
            text = next((b.text for b in response.content if hasattr(b, 'text')), '')
            return jsonify({'response': text})

        if response.stop_reason == 'tool_use':
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == 'tool_use':
                    fn = TOOL_FNS.get(block.name)
                    result = fn(block.input) if fn else f"Unknown tool: {block.name}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })
            messages.append({"role": "user", "content": tool_results})

    return jsonify({'response': 'Done.'})
