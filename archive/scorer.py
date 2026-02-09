import pandas as pd

def score_round(preds_df: pd.DataFrame,
                race_df: pd.DataFrame,
                is_sprint_weekend: bool) -> pd.DataFrame:
    """
    preds_df columns (from your sheet):
        - 'F1 Round'
        - 'Name'
        - 'First Choice'
        - 'Second Choice'
        - 'Third Choice'
        - 'Would you like to play your JOKER for double points?'

    race_df columns (from mock/API results):
        - 'Driver'
        - 'Position'
        - 'MainPoints'
        - 'SprintPoints'
    """

    # Normalise column names we’ll use
    preds = preds_df.copy()
    race = race_df.copy()

    # Make a quick lookup for driver → points / position
    race = race.set_index('Driver')

    results = []

    for _, row in preds.iterrows():
        name = row['Name']
        round_num = row['F1 Round']

        first = str(row['First Choice']).strip()
        second = str(row['Second Choice']).strip()
        third = str(row['Third Choice']).strip()

        joker_raw = str(row['Would you like to play your JOKER for double points?']).strip().lower()
        joker_played = joker_raw in ['yes', 'y', 'true', '1']

        # --- 1. Base points from drivers ---

        def get_driver_points(driver_name):
            if driver_name in race.index:
                main_pts = race.loc[driver_name, 'MainPoints']
                sprint_pts = race.loc[driver_name, 'SprintPoints'] if is_sprint_weekend else 0
                pos = race.loc[driver_name, 'Position']
                return main_pts, sprint_pts, pos
            else:
                # Driver not found in results (e.g. DNF or typo)
                return 0, 0, None

        first_main, first_sprint, first_pos = get_driver_points(first)
        second_main, second_sprint, second_pos = get_driver_points(second)
        third_main, third_sprint, third_pos = get_driver_points(third)

        main_points = first_main + second_main + third_main
        sprint_points = first_sprint + second_sprint + third_sprint

        # --- 2. Order bonus ---

        # Get actual top 3 in order from race_df
        actual_top3 = (
            race_df.sort_values('Position')
                   .head(3)['Driver']
                   .tolist()
        )

        predicted_top3 = [first, second, third]

        order_bonus = 0
        if predicted_top3 == actual_top3:
            order_bonus = 40
        elif predicted_top3[:2] == actual_top3[:2]:
            order_bonus = 20
        elif predicted_top3[0] == actual_top3[0]:
            order_bonus = 10

        # --- 3. Joker logic ---

        joker_multiplier = 2 if joker_played else 1

        # Only main race + bonus are doubled
        total_round_score = (main_points + order_bonus) * joker_multiplier + sprint_points

        results.append({
            'Round': round_num,
            'Name': name,
            'Main Points': main_points,
            'Sprint Points': sprint_points,
            'Order Bonus': order_bonus,
            'Joker Played': 'Yes' if joker_played else 'No',
            'Total Round Score': total_round_score
        })

    scores_df = pd.DataFrame(results)
    return scores_df