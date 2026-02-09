import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# ------------------------------------------------------------
# Helper: Normalise driver names (compare by last name only)
# ------------------------------------------------------------
def normalize(name):
    name = str(name).strip().lower()
    parts = name.split()
    return parts[-1]  # last name only


def update_standings(spreadsheet_id, credentials_file):

    # --- Authorize Google Sheets ---
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)

    # --- Load Predictions ---
    predictions_ws = sh.worksheet("Predictions")
    predictions_df = pd.DataFrame(predictions_ws.get_all_records())

    # --- Load Race Results ---
    results_ws = sh.worksheet("Mock_API_Results")
    results_df = pd.DataFrame(results_ws.get_all_records())

    # --- Detect all rounds dynamically ---
    all_rounds = sorted(predictions_df["F1 Round"].unique())

    # --- Prepare Player_Standings output ---
    player_rows = []

    # ------------------------------------------------------------
    # MAIN SCORING LOOP
    # ------------------------------------------------------------
    for rnd in all_rounds:

        round_preds = predictions_df[predictions_df["F1 Round"] == rnd]
        round_results = results_df[results_df["Round"] == rnd]

        # Lookup maps
        main_points_map = dict(zip(round_results["Driver"], round_results["MainPoints"]))
        sprint_points_map = dict(zip(round_results["Driver"], round_results["SprintPoints"]))

        # Correct finishing order
        finishing_order = list(round_results.sort_values("Position")["Driver"])
        finishing_order_norm = [normalize(d) for d in finishing_order]

        # Score each player
        for _, row in round_preds.iterrows():

            name = row["Name"]
            first = row["First Choice"]
            second = row["Second Choice"]
            third = row["Third Choice"]

            joker_raw = str(row["Would you like to play your JOKER for double points?"]).strip().lower()
            joker_played = joker_raw in ["yes", "y", "true", "1"]

            # --- Main Points ---
            main_total = (
                main_points_map.get(first, 0)
                + main_points_map.get(second, 0)
                + main_points_map.get(third, 0)
            )

            # --- Sprint Points ---
            sprint_total = (
                sprint_points_map.get(first, 0)
                + sprint_points_map.get(second, 0)
                + sprint_points_map.get(third, 0)
            )

            # ------------------------------------------------------------
            # ORDER BONUS (winner-first logic)
            # ------------------------------------------------------------
            predicted_norm = [
                normalize(first),
                normalize(second),
                normalize(third)
            ]

            # Winner must be correct to earn ANY bonus
            if predicted_norm[0] == finishing_order_norm[0]:

                # Winner correct → check 2nd
                if predicted_norm[1] == finishing_order_norm[1]:

                    # 1st + 2nd correct → check 3rd
                    if predicted_norm[2] == finishing_order_norm[2]:
                        order_bonus = 40   # Perfect top 3
                    else:
                        order_bonus = 20   # Correct 1st + 2nd

                else:
                    order_bonus = 10       # Correct winner only

            else:
                order_bonus = 0            # No bonus at all

            # --- Total Round Score (with Joker rule) ---
            if joker_played:
                total_round_score = (main_total + order_bonus) * 2 + sprint_total
            else:
                total_round_score = main_total + order_bonus + sprint_total

            # Append row
            player_rows.append({
                "F1 Round": rnd,
                "Contestant Name": name,
                "Total Round Score": total_round_score,
                "Sprint Points": sprint_total,
                "Order Bonus": order_bonus,
                "Joker Played": "Yes" if joker_played else "No"
            })

    # ------------------------------------------------------------
    # BUILD PLAYER_STANDINGS SHEET
    # ------------------------------------------------------------
    player_standings_df = pd.DataFrame(player_rows)

    try:
        sh.del_worksheet(sh.worksheet("Player_Standings"))
    except:
        pass

    new_ws = sh.add_worksheet(title="Player_Standings", rows="500", cols="20")
    new_ws.update(
        [player_standings_df.columns.values.tolist()]
        + player_standings_df.values.tolist()
    )

    # ------------------------------------------------------------
    # BUILD CUMULATIVE STANDINGS
    # ------------------------------------------------------------
    player_standings_df = player_standings_df.sort_values(["Contestant Name", "F1 Round"])

    player_standings_df["Cumulative Score"] = (
        player_standings_df.groupby("Contestant Name")["Total Round Score"].cumsum()
    )

    standings_output = player_standings_df.rename(columns={
        "Contestant Name": "Name"
    })

    try:
        sh.del_worksheet(sh.worksheet("Standings"))
    except:
        pass

    standings_ws = sh.add_worksheet(title="Standings", rows="500", cols="20")
    standings_ws.update(
        [standings_output.columns.values.tolist()]
        + standings_output.values.tolist()
    )

    # ------------------------------------------------------------
    # RETURN LATEST ROUND + CAR RESULTS
    # ------------------------------------------------------------
    standings_output = standings_output.sort_values("F1 Round")
    standings_output = standings_output.groupby("Name", as_index=False).last()

    ROUND_TO_SHOW = standings_output["F1 Round"].max()

    latest_results = results_df[results_df["Round"] == ROUND_TO_SHOW]
    car_results = list(latest_results.sort_values("Position")["Driver"])

    return standings_output, car_results, ROUND_TO_SHOW