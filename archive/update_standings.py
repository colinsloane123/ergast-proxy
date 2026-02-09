import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials


def update_player_standings(sheet_id: str, scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Loads the existing standings from Google Sheets,
    merges them with the new round scores,
    updates totals, and writes the updated standings back.
    """

    # --- 1. Authenticate ---
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gc = gspread.authorize(creds)

    # --- 2. Load existing standings sheet ---
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet("Standings")

    data = ws.get_all_records()
    old_df = pd.DataFrame(data)

    # Ensure required columns exist
    required_cols = ["Name", "Total Points"]

    for col in required_cols:
        if col not in old_df.columns:
            old_df[col] = 0

    # Keep only required columns in correct order
    old_df = old_df[required_cols]

    # --- 3. Merge new scores with old standings ---
    old_df["Name"] = old_df["Name"].astype(str)
    scores_df["Name"] = scores_df["Name"].astype(str)

    # Sum total round score per player
    round_totals = scores_df.groupby("Name")["Total Round Score"].sum().reset_index()

    # Merge with existing standings
    combined = pd.merge(old_df, round_totals, on="Name", how="outer")

    # Replace missing totals with 0
    combined["Total Points"] = combined["Total Points"].fillna(0)
    combined["Total Round Score"] = combined["Total Round Score"].fillna(0)

    # Update total points
    combined["Total Points"] = (
        combined["Total Points"].astype(float) +
        combined["Total Round Score"].astype(float)
    )

    # Sort by total points descending
    combined = combined.sort_values("Total Points", ascending=False)

    # --- 4. Clean ALL NaN / None / NaT values before upload ---
    combined = combined.replace({float('nan'): "", None: "", pd.NA: ""}).fillna("")

    # Convert everything to string (Google Sheets safe)
    combined = combined.astype(str)

    # --- 5. Upload back to Google Sheets ---
    ws.update(
        [combined.columns.values.tolist()] +
        combined.values.tolist()
    )

    return combined