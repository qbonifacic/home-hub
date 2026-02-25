"""Set up Google Sheets tabs with headers for Home Hub."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.sheets import _get_client, SHEET_ID

TABS = {
    'MealPlan': ['day', 'meal_type', 'meal'],
    'Recipes': ['meal_name', 'ingredients_json', 'instructions', 'fat_g', 'protein_g', 'net_carbs_g'],
    'Chores': ['task', 'frequency', 'last_done', 'next_due', 'assigned'],
    'Reminders': ['Title', 'Due Date', 'Completed', 'Created'],
}


def setup():
    client = _get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    existing = [ws.title for ws in spreadsheet.worksheets()]

    for tab_name, headers in TABS.items():
        if tab_name in existing:
            ws = spreadsheet.worksheet(tab_name)
            first_row = ws.row_values(1)
            if not first_row:
                ws.update([headers], 'A1')
                print(f"  Added headers to existing tab: {tab_name}")
            else:
                print(f"  Tab already exists with data: {tab_name}")
        else:
            ws = spreadsheet.add_worksheet(title=tab_name, rows=100, cols=len(headers))
            ws.update([headers], 'A1')
            print(f"  Created tab: {tab_name}")

    print("Sheet setup complete.")


if __name__ == '__main__':
    setup()
