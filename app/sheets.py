import json
import os

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = os.environ.get('SHEET_ID', '1pgFsQUT6_pK5I5dZU1S_eyqwDBBdndDd9LkB69MW6R0')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

_client = None


def _get_client():
    global _client
    if _client is None:
        creds_json = os.environ.get('GOOGLE_CREDS_JSON')
        if creds_json:
            info = json.loads(creds_json)
        else:
            with open(os.path.join(os.path.dirname(__file__), '..', 'google_creds.json')) as f:
                info = json.load(f)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        _client = gspread.authorize(creds)
    return _client


def get_worksheet(tab_name):
    client = _get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    return spreadsheet.worksheet(tab_name)


def get_all_records(tab_name):
    ws = get_worksheet(tab_name)
    return ws.get_all_records()


def append_row(tab_name, row):
    ws = get_worksheet(tab_name)
    ws.append_row(row, value_input_option='USER_ENTERED')


def update_cell(tab_name, row, col, value):
    ws = get_worksheet(tab_name)
    ws.update_cell(row, col, value)


def delete_row(tab_name, row_index):
    ws = get_worksheet(tab_name)
    ws.delete_rows(row_index)
