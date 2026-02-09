import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import imageio.v2 as imageio
import warnings
import numpy as np
from PIL import Image
from matplotlib import patches

warnings.filterwarnings("ignore", category=RuntimeWarning)

# --- CONFIG ---

STANDINGS_SHEET = 'Standings'
CALENDAR_SHEET = 'Race_Calendar'
PREDICTIONS_SHEET = 'Predictions'
MOCK_API_SHEET = 'Mock_API_Results'

FPS = 30
PODIUM_FRAMES = 210
BAR_FRAMES = 150
final_hold_frames = 600  # final slate hold

def run(cfg):
    global SPREADSHEET_ID, CREDENTIALS_FILE, CARS_FOLDER, OUTPUT_FOLDER

    # Load config
    SPREADSHEET_ID = cfg["spreadsheet_id"]
    CREDENTIALS_FILE = cfg["credentials_file"]
    CARS_FOLDER = cfg["cars_folder"]
    OUTPUT_FOLDER = cfg["output_folder"]

    # --- AUTH ---
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE, scope
    )
    client = gspread.authorize(creds)

    # --- LOAD DATA ---
    ss = client.open_by_key(SPREADSHEET_ID)

    standings_df = pd.DataFrame(ss.worksheet(STANDINGS_SHEET).get_all_records())
    calendar_df = pd.DataFrame(ss.worksheet(CALENDAR_SHEET).get_all_records())
    race_df = pd.DataFrame(ss.worksheet(MOCK_API_SHEET).get_all_records())
    predictions_df = pd.DataFrame(ss.worksheet(PREDICTIONS_SHEET).get_all_records())

    # --- JOKER LOOKUP ---
    joker_lookup = {}
    for _, row in predictions_df.iterrows():
        name = str(row.get("Name", "")).strip()
        joker_response = str(
            row.get("Would you like to play your JOKER for double points?", "")
        ).strip().lower()
        if joker_response == "yes":
            joker_lookup[name] = True

    # --- CAR RESULTS ---
    def normalise_driver_name(name):
        name = str(name).strip()
        parts = name.split()
        return parts[-1]

    car_results = []
    if "Driver" in race_df.columns and "Team" in race_df.columns:
        for _, row in race_df.iterrows():
            driver_raw = str(row["Driver"]).strip()
            driver = normalise_driver_name(driver_raw)
            team = str(row["Team"]).strip()
            car_results.append((driver, team))

    # --- ROUND INFO ---
    ROUND_TO_SHOW = int(standings_df["F1 Round"].max())

    players_bar = (
        standings_df.sort_values("F1 Round")
        .groupby("Name", as_index=False)
        .tail(1)
        .sort_values("Cumulative Score", ascending=True)
        .reset_index(drop=True)
    )

    # --- BAR + PODIUM SETUP ---
    num_players = len(players_bar)
    max_pts = players_bar["Cumulative Score"].max()

    # Podium: top 3 from standings
    podium_players = players_bar.tail(3).iloc[::-1].reset_index(drop=True)

    # --- NEXT RACE DETAILS ---
    next_round_num = ROUND_TO_SHOW + 1
    race_name = "TBC"
    race_dates = ""

    for _, row in calendar_df.iterrows():
        try:
            r = int(row["Round"])
        except Exception:
            continue
        if r == next_round_num:
            race_name = str(row["Race Name"])
            start = str(row["Start Date"])
            end = str(row["End Date"])
            race_dates = start if start == end else f"{start} - {end}"
            break

    next_race_text = f"NEXT RACE = ROUND {next_round_num} {race_name.upper()} {race_dates}"
    letters = list(next_race_text)
    num_letters = len(letters)

    max_width = 0.85
    letter_spacing = max_width / max(1, num_letters)
    x_positions = np.linspace(
        0.5 - (letter_spacing * num_letters) / 2,
        0.5 + (letter_spacing * num_letters) / 2,
        num_letters
    )

    letter_stagger = 2
    bounce_duration = 20
    closing_frames = (num_letters * letter_stagger) + bounce_duration + 20

    def bounce_ease(t):
        return 1 - np.exp(-4 * t) * np.cos(10 * t)

    def make_white_transparent(path):
        img = Image.open(path).convert("RGBA")
        data = np.array(img)
        r, g, b, a = data.T
        white_areas = (r > 240) & (g > 240) & (b > 240)
        data[..., -1][white_areas.T] = 0
        return Image.fromarray(data)

    # ------------------------------------------------------------
    # PODIUM
    # (your animation loops continue here…)
# ------------------------------------------------------------
def draw_podium(fig, f, ROUND_TO_SHOW, podium_players, car_results):
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_facecolor('white')

    freeze_f = min(f, 60)
    rise_progress = min(1, freeze_f / 20)

    alpha_title = min(1, freeze_f / 10)
    fig.text(
        0.5, 0.9,
        f"F1 Fantasy – Round {ROUND_TO_SHOW} Podium",
        color='#222222', size=30, weight='bold',
        ha='center', alpha=alpha_title
    )

    podium_x = [0.35, 0.5, 0.65]
    heights = [0.25, 0.35, 0.2]
    colors = ['#c0c0ff', '#ffd700', '#ffb347']

    for i, h in enumerate(heights):
        base_y = 0.15
        ax.add_patch(
            plt.Rectangle(
                (podium_x[i] - 0.06, base_y),
                0.12,
                h * rise_progress,
                color=colors[i],
                ec='#444444',
                linewidth=2
            )
        )

    if freeze_f > 10:
        for idx, row in podium_players.iterrows():
            px_idx = 1 if idx == 0 else (0 if idx == 1 else 2)
            x = podium_x[px_idx]
            h = heights[px_idx]
            base_y = 0.15
            top_y = base_y + h * rise_progress

            if idx < len(car_results):
                driver_name, team_name = car_results[idx]
                # ✅ Now shimmer can safely use x and top_y
                shimmer = patches.Circle(
                    (x, top_y - 0.05),
                    radius=0.12,
                    color=TEAM_COLOURS.get(team_name.lower(), TEAM_COLOURS['generic']),
                    alpha=0.25,
                    zorder=0
                )
                ax.add_patch(shimmer)


                img_path = os.path.join(CARS_FOLDER, f"{driver_name}.png")

                if os.path.exists(img_path):
                    try:
                        car_img = make_white_transparent(img_path)
                        im = OffsetImage(car_img, zoom=0.4)

                        car_y = base_y + (top_y - base_y) * rise_progress + 0.05

                        ab = AnnotationBbox(
                            im, (x, car_y),
                            frameon=False, box_alignment=(0.5, 0)
                        )
                        ax.add_artist(ab)
                    except Exception:
                        pass

            name = row['Name']
            pts = int(row['Cumulative Score'])
            text_alpha = min(1, (freeze_f - 10) / 10)

            ax.text(
                x, top_y + 0.13, name,
                ha='center', va='bottom',
                color='#222222', weight='bold',
                fontsize=16, alpha=text_alpha
            )

            ax.text(
                x, top_y + 0.18, f"{pts} pts",
                ha='center', va='bottom',
                color='#444444', weight='bold',
                fontsize=14,
                alpha=text_alpha
            )

    if freeze_f >= 15:
        np.random.seed(42)
        n_confetti = 80
        xs = np.random.rand(n_confetti)
        ys = 0.4 + 0.6 * np.random.rand(n_confetti)
        colors_conf = np.random.choice(
            ['#ff4b81', '#ffd700', '#7df9ff', '#b19cd9'],
            n_confetti
        )
        sizes = 10 + 40 * np.random.rand(n_confetti)
        ax.scatter(xs, ys, c=colors_conf, s=sizes, alpha=0.6)

    if freeze_f >= 15:
        n_confetti = 80

        # Random horizontal positions (stay the same each frame)
        xs = np.random.rand(n_confetti)

        # Falling vertical positions
        # Start high, then fall downward as freeze_f increases
        ys = 0.4 + 0.6 * np.random.rand(n_confetti) - 0.015 * (freeze_f - 15)

        colors_conf = np.random.choice(
            ['#ff4b81', '#ffd700', '#7df9ff', '#b19cd9'],
            n_confetti
        )
        sizes = 10 + 40 * np.random.rand(n_confetti)

        ax.scatter(xs, ys, c=colors_conf, s=sizes, alpha=0.6)

TEAM_COLOURS = {
    'mercedes': '#00D2BE',
    'red bull': '#1E41FF',
    'ferrari': '#DC0000',
    'mclaren': '#FF6C0A',      # Papaya Orange
    'aston martin': '#006F62',
    'alpine': '#0090FF',
    'williams': '#005AFF',
    'stake': '#52E252',
    'rb': '#6692FF',
    'haas': '#B6BABD',
    'generic': '#007acc'
}
# ------------------------------------------------------------
# BARS
# ------------------------------------------------------------
def draw_bars_full(fig, progress, max_pts, players_bar, num_players, ROUND_TO_SHOW, car_results, joker_lookup):
    ax = fig.add_axes([0.15, 0.2, 0.75, 0.65])
    ax.set_xlim(0, max_pts + 50)
    ax.set_ylim(-0.5, num_players - 0.5)
    ax.set_yticks(range(num_players))
    ax.set_yticklabels(players_bar['Name'], color='black', weight='bold', fontsize=14)
    ax.set_facecolor('white')

    fig.text(
        0.5, 0.9,
        f'F1 Fantasy Round {ROUND_TO_SHOW}: Cumulative Standings',
        color='black', size=28, weight='bold', ha='center'
    )

    ax.spines['bottom'].set_color('#cccccc')
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis='x', colors='black', labelsize=12)

    # ------------------------------------------------------------
    # MAIN LOOP — EVERYTHING BELOW MUST BE INSIDE THIS LOOP
    # ------------------------------------------------------------
    for i, (index, row) in enumerate(players_bar.iterrows()):

        player_name = row['Name']

        # ------------------------------------------------------------
        # TEAM COLOUR + ANIMATED BAR FILL
        # ------------------------------------------------------------
        rank_from_top = (num_players - 1) - i

        if rank_from_top < len(car_results):
            driver_name, team_name = car_results[rank_from_top]

            # Normalise team name for lookup
            team_key = team_name.lower().strip()

            bar_color = TEAM_COLOURS.get(team_key, TEAM_COLOURS['generic'])
        else:
            bar_color = TEAM_COLOURS['Generic']

        # Smooth easing for nicer animation
        def ease_out_cubic(t):
            return 1 - (1 - t)**3

        eased_progress = ease_out_cubic(progress)

        current_x = row['Cumulative Score'] * eased_progress

        ax.barh(
            i, current_x,
            color=bar_color, height=0.6,
            edgecolor='black', linewidth=1, zorder=1
        )

        ax.text(
            current_x + 5, i,
            f"{int(current_x)} pts",
            color='black',
            va='center', weight='bold', zorder=2
        )

        # ------------------------------------------------------------
        # JOKER BADGE
        if joker_lookup.get(player_name, False):
            ax.text(
                5, i,
                "JOKER PLAYED",
                color='white',
                fontsize=12,
                weight='bold',
                va='center',
                ha='left',
                zorder=5
            )

        # ------------------------------------------------------------
        # CAR + DRIVER NAME
        # ------------------------------------------------------------
        if rank_from_top < len(car_results):
            driver_name, team_name = car_results[rank_from_top]
            img_path = os.path.join(CARS_FOLDER, f"{driver_name}.png")

            if os.path.exists(img_path):
                try:
                    car_img = Image.open(img_path)

                    # Car sits inside the bar
                    car_x = current_x - 40
                    im = OffsetImage(car_img, zoom=0.30, resample=True)

                    ab = AnnotationBbox(
                        im, (car_x, i),
                        frameon=False,
                        box_alignment=(0.5, 0.5),
                        zorder=3
                    )
                    ax.add_artist(ab)

                    # Driver name behind the car with dynamic spacing
                    min_gap = 25          # minimum distance behind the car
                    relative_gap = current_x * 0.12   # scales with bar length

                    name_x = car_x - max(min_gap, relative_gap)

                    ax.text(
                        name_x,
                        i,
                        driver_name.upper(),
                        color='white',
                        fontsize=12,
                        weight='bold',
                        va='center',
                        ha='right',   # aligns neatly toward the car
                        zorder=4
                    )

                except Exception:
                    pass

    return ax


def run(cfg):
    global SPREADSHEET_ID, CREDENTIALS_FILE, CARS_FOLDER, OUTPUT_FOLDER

    # --- LOAD CONFIG VALUES ---
    SPREADSHEET_ID = cfg["spreadsheet_id"]
    CREDENTIALS_FILE = cfg["credentials_file"]
    CARS_FOLDER = cfg["cars_folder"]
    OUTPUT_FOLDER = cfg["output_folder"]

    # --- AUTH ---
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    # --- LOAD DATA ---
    ss = client.open_by_key(SPREADSHEET_ID)
    standings_df = pd.DataFrame(ss.worksheet(STANDINGS_SHEET).get_all_records())
    calendar_df = pd.DataFrame(ss.worksheet(CALENDAR_SHEET).get_all_records())
    race_df = pd.DataFrame(ss.worksheet(MOCK_API_SHEET).get_all_records())
    predictions_df = pd.DataFrame(ss.worksheet(PREDICTIONS_SHEET).get_all_records())

    # --- JOKER LOOKUP ---
    joker_lookup = {}
    for _, row in predictions_df.iterrows():
        name = str(row.get("Name", "")).strip()
        joker_response = str(row.get("Would you like to play your JOKER for double points?", "")).strip().lower()
        if joker_response == "yes":
            joker_lookup[name] = True

    # --- CAR RESULTS ---
    def normalise_driver_name(name):
        name = str(name).strip()
        parts = name.split()
        return parts[-1]

    car_results = []
    if "Driver" in race_df.columns and "Team" in race_df.columns:
        for _, row in race_df.iterrows():
            driver_raw = str(row["Driver"]).strip()
            driver = normalise_driver_name(driver_raw)
            team = str(row["Team"]).strip()
            car_results.append((driver, team))

    # --- ROUND INFO ---
    ROUND_TO_SHOW = int(standings_df["F1 Round"].max())

    players_bar = (
        standings_df.sort_values("F1 Round")
        .groupby("Name", as_index=False)
        .tail(1)
        .sort_values("Cumulative Score", ascending=True)
        .reset_index(drop=True)
    )

    # --- BAR + PODIUM SETUP ---
    num_players = len(players_bar)
    max_pts = players_bar["Cumulative Score"].max()
    podium_players = players_bar.tail(3).iloc[::-1].reset_index(drop=True)

    # --- NEXT RACE DETAILS ---
    next_round_num = ROUND_TO_SHOW + 1
    race_name = "TBC"
    race_dates = ""
    for _, row in calendar_df.iterrows():
        try:
            r = int(row["Round"])
        except Exception:
            continue
        if r == next_round_num:
            race_name = str(row["Race Name"])
            start = str(row["Start Date"])
            end = str(row["End Date"])
            race_dates = start if start == end else f"{start} - {end}"
            break

    next_race_text = f"NEXT RACE = ROUND {next_round_num} {race_name.upper()} {race_dates}"
    letters = list(next_race_text)
    num_letters = len(letters)

    max_width = 0.85
    letter_spacing = max_width / max(1, num_letters)
    x_positions = np.linspace(
        0.5 - (letter_spacing * num_letters) / 2,
        0.5 + (letter_spacing * num_letters) / 2,
        num_letters
    )

    letter_stagger = 2
    bounce_duration = 20
    closing_frames = (num_letters * letter_stagger) + bounce_duration + 20

    def bounce_ease(t):
        return 1 - np.exp(-4 * t) * np.cos(10 * t)

    def make_white_transparent(path):
        img = Image.open(path).convert("RGBA")
        data = np.array(img)
        r, g, b, a = data.T
        white_areas = (r > 240) & (g > 240) & (b > 240)
        data[..., -1][white_areas.T] = 0
        return Image.fromarray(data)

    # --- VIDEO WRITER ---
    output_name = os.path.join(
        OUTPUT_FOLDER,
        f"F1_Round_{ROUND_TO_SHOW}_Pro.mp4"
    )
    writer = imageio.get_writer(output_name, fps=FPS)

    # ------------------------------------------------------------
    # MAIN: PODIUM + BARS
    # ------------------------------------------------------------
    total_frames = PODIUM_FRAMES + BAR_FRAMES
    print(f"Rendering podium + bars ({total_frames} frames)...")

    for f in range(total_frames):
        plt.close('all')
        fig = plt.figure(figsize=(16, 9.12), facecolor='white')
        fig.patch.set_facecolor('white')

        if f < PODIUM_FRAMES:
            draw_podium(fig, f, ROUND_TO_SHOW, podium_players, car_results)
        else:
            frame_idx = f - PODIUM_FRAMES
            progress = min(1.0, frame_idx / BAR_FRAMES)
            draw_bars_full(fig, progress, max_pts, players_bar, num_players, ROUND_TO_SHOW, car_results, joker_lookup)

        fig.canvas.draw()
        frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
        writer.append_data(frame)
        plt.close(fig)

    bar_chart_frame = frame.copy()
    print("Captured final bar chart frame.")

    # ------------------------------------------------------------
    # NEXT RACE BOUNCE
    # ------------------------------------------------------------
    print("Rendering NEXT RACE bounce slate...")

    for f in range(closing_frames):
        plt.close('all')
        fig = plt.figure(figsize=(16, 9.12), facecolor='white')
        fig.patch.set_facecolor('white')

        draw_bars_full(
        fig,
        progress=1.0,
        max_pts=max_pts,
        players_bar=players_bar,
        num_players=num_players,
        ROUND_TO_SHOW=ROUND_TO_SHOW,
        car_results=car_results,
        joker_lookup=joker_lookup
    )
        

        for i, letter in enumerate(letters):
            start_frame = i * letter_stagger
            if f < start_frame:
                continue

            t = min(1.0, (f - start_frame) / bounce_duration)
            b = bounce_ease(t)

            start_y = -0.2
            end_y = 0.08
            y = start_y + b * (end_y - start_y)

            txt = fig.text(
                x_positions[i], y,
                letter,
                color='#E10600',
                size=32, weight='black', ha='center', zorder=100
            )
            txt.set_path_effects([patheffects.withStroke(linewidth=2, foreground='white')])

        fig.canvas.draw()
        frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
        writer.append_data(frame)
        plt.close(fig)

    final_bounce_frame = frame.copy()
    print("Captured final NEXT RACE slate frame.")

    # ------------------------------------------------------------
    # FINAL HOLD
    # ------------------------------------------------------------
    print(f"Holding final slate for {final_hold_frames} frames...")

    for _ in range(final_hold_frames):
        writer.append_data(final_bounce_frame)

    writer.close()
    print(f"🏁 DONE! Video saved as: {output_name}")


