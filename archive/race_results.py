import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def fetch_mock_race_results(sheet_id: str, round_num: int, credentials_file="credentials.json"):
    """
    Loads mock race results for testing.
    Expects a sheet/tab named 'Mock_API_Results' with columns:
        - Driver
        - Position
        - MainPoints
        - SprintPoints
    """

    # Google Sheets auth
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    gc = gspread.authorize(creds)

    # Open the sheet
    ws = gc.open_by_key(sheet_id).worksheet("Mock_API_Results")

    # Convert to DataFrame
    df = pd.DataFrame(ws.get_all_records())

    # If your mock sheet includes a Round column, filter by round
    if "Round" in df.columns:
        df = df[df["Round"] == round_num]

    # Sort by finishing position
    df = df.sort_values("Position").reset_index(drop=True)

    return df
import os

CARS_FOLDER = r"C:\F1_Project\cars"

def get_car_image_path(driver_name: str) -> str:
    """
    Map a driver name like 'Max Verstappen' or 'VER' to the correct car image path.
    Assumes files are named like 'Verstappen.png', 'Norris.png', etc.
    """
    # Take surname only
    surname = driver_name.split()[-1]

    # Normalise: capitalise first letter, rest lower
    filename = surname.capitalize() + ".png"

    return os.path.join(CARS_FOLDER, filename)