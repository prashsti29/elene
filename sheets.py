# sheets.py

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from state import CallerState
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = os.getenv("GOOGLE_SHEETS_ID")

def get_sheets_client():
    creds = Credentials.from_service_account_file("elenecredentials.json", scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)

async def save_to_sheets(state: CallerState):
    client = get_sheets_client()
    
    row = [[
        state.name,
        state.phone,
        state.email,
        state.role,
        state.property_type
    ]]
    
    client.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="Sheet1!A:E",
        valueInputOption="RAW",
        body={"values": row}
    ).execute()