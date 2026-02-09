import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from animation import generate_animation


# -----------------------------
# Google Sheets Configuration
# -----------------------------
CREDENTIALS_FILE = 'credentials.json'
SPREADSHEET_ID = '1sv-FwCgWADXw1oTkaVgA2QLOWPoSc3v3z0vx0UOUhxE'

PLAYER_SHEET = 'Standings'
RACE_SHEET = 'Mock_API_Results'
CALENDAR_SHEET = 'Race_Calendar'


# -----------------------------
# Connect to Google Sheets
# -----------------------------
def load_sheet(sheet_name):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    gc = gspread.authorize(creds)

    ws = gc.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
    df = pd.DataFrame(ws.get_all_records())
    return df


# -----------------------------
# Next Race Text Helper
# -----------------------------
def get_next_race_text(calendar_df, round_num):
    next_round = round_num + 1
    row = calendar_df[calendar_df["Round"] == next_round]

    if row.empty:
        return "Season Complete"

    row = row.iloc[0]
    race_name = row["Race Name"]

    start = pd.to_datetime(row["Start Date"], dayfirst=True).strftime("%#d %B")
    end = pd.to_datetime(row["End Date"], dayfirst=True).strftime("%#d %B")

    return f"Next Race: {race_name} — {start}–{end}"


# -----------------------------
# Load DataFrames from Sheets
# -----------------------------
standings_df = load_sheet(PLAYER_SHEET)
race_df = load_sheet(RACE_SHEET)
calendar_df = load_sheet(CALENDAR_SHEET)

# Convert date columns
calendar_df["Start Date"] = pd.to_datetime(calendar_df["Start Date"], dayfirst=True)
calendar_df["End Date"] = pd.to_datetime(calendar_df["End Date"], dayfirst=True)

# Determine current round from race results
round_num = int(race_df["Round"].iloc[0])

# Compute footer text
next_race_text = get_next_race_text(calendar_df, round_num)


# -----------------------------
# Generate Animation
# -----------------------------
generate_animation(
    standings_df,
    race_df,
    round_num,
    next_race_text
)