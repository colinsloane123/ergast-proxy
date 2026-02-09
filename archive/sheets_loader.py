import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def load_predictions(sheet_id: str, round_num: int, credentials_file="credentials.json"):
    """
    Loads predictions for a specific round from the 'Predictions' sheet.
    Returns a DataFrame ready for scoring.
    """

    # Google Sheets auth
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    gc = gspread.authorize(creds)

    # Open the sheet
    ws = gc.open_by_key(sheet_id).worksheet("Predictions")

    # Convert to DataFrame
    df = pd.DataFrame(ws.get_all_records())

    # Filter for the round we want
    df_round = df[df["F1 Round"] == round_num].copy()

    return df_round