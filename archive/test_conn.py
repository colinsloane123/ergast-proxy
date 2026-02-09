import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# CONFIG
BASE_PATH = r'C:\F1_Project'
CREDENTIALS_FILE = os.path.join(BASE_PATH, 'credentials.json')
SPREADSHEET_ID = '1sv-FwCgWADXw1oTkaVgA2QLOWPoSc3v3z0vx0UOUhxE'.strip()

def test_connection():
    print(f"🔍 Checking for credentials at: {CREDENTIALS_FILE}")
    if not os.path.exists(CREDENTIALS_FILE):
        print(r"❌ ERROR: credentials.json not found in C:\F1_Project")

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        gc = gspread.authorize(creds)
        ss = gc.open_by_key(SPREADSHEET_ID)
        ws = ss.worksheet('Player_Standings')
        data = ws.row_values(2) # Try to read the first row of data
        print("✅ SUCCESS! Connected to Google Sheets.")
        print(f"📊 Sample Data Found: {data}")
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {e}")

if __name__ == "__main__":
    test_connection()