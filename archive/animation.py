from moviepy.editor import VideoClip, ImageClip, CompositeVideoClip, ColorClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from race_results import get_car_image_path


def make_text_image(text, fontsize=40, color="black", font="arial.ttf"):
    font = ImageFont.truetype(font, fontsize)
    dummy_img = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    img = Image.new("RGBA", (w + 10, h + 10), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((5, 5), text, font=font, fill=color)
    return ImageClip(np.array(img)), h


def generate_animation(
    standings_df,
    race_df,
    round_num,
    next_race_text,
    output_path="round_animation.mp4"
):
    WIDTH, HEIGHT = 1280, 720
    DURATION = 6
    BAR_HEIGHT = 40

    bg = ColorClip(size=(WIDTH, HEIGHT), color=(255, 255, 255)).set_duration(DURATION)

    # Header
    title, _ = make_text_image(
        f"F1 Standings — After Round {round_num}",
        fontsize=60,
        color="black",
        font="arialbd.ttf"
    )
    title = title.set_position(("center", 20)).set_duration(DURATION)

    # Bars
    bar_clips = []
    spacing = HEIGHT // (len(standings_df) + 4)
    max_score = standings_df["Cumulative Score"].astype(float).max()
    top_index = standings_df["Cumulative Score"].astype(float).idxmax()
    bar_end_positions = []

    for i, (idx, row) in enumerate(standings_df.iterrows()):
        name = row["Name"]
        score = float(row["Cumulative Score"])
        y_pos = spacing * (i + 1) + 80
        bar_width = int((score / max_score) * 500) if max_score > 0 else 1
        bar_end_positions.append((y_pos, bar_width))
        bar_color = (0, 180, 0) if idx == top_index else (0, 120, 255)

        bar = ColorClip(size=(bar_width, BAR_HEIGHT), color=bar_color).set_duration(DURATION)
        bar = bar.set_position((100, y_pos))

        name_clip, name_height = make_text_image(name, fontsize=28, color="black", font="arial.ttf")
        name_clip = name_clip.set_position((20, y_pos + (BAR_HEIGHT - name_height) // 2)).set_duration(DURATION)

        score_clip, _ = make_text_image(str(int(score)), fontsize=32, color="black", font="arial.ttf")
        score_clip = score_clip.set_position((100 + bar_width + 15, y_pos)).set_duration(DURATION)

        bar_clips.extend([bar, name_clip, score_clip])

    # Cars
    car_clips = []
    BASE_CAR_WIDTH = 120
    race_df = race_df.head(len(standings_df))

    for i, (_, row) in enumerate(race_df.iterrows()):
        driver = row["Driver"]
        car_path = get_car_image_path(driver)
        y_pos, bar_width = bar_end_positions[i]
        car_width = min(BASE_CAR_WIDTH, bar_width - 10)

        car_img = Image.open(car_path).convert("RGBA")
        w, h = car_img.size
        new_h = int(h * (car_width / w))
        car_img = car_img.resize((car_width, new_h), Image.Resampling.LANCZOS)

        car_y = y_pos + (BAR_HEIGHT - new_h) // 2
        stop_x = 100 + bar_width - car_width - 5

        car_clip = ImageClip(np.array(car_img)).set_duration(DURATION)

        def make_position_func(y, stop_x):
            def pos(t):
                progress = min(t / (DURATION * 0.7), 1)
                x = -400 + (stop_x + 400) * progress
                return (int(x), y)
            return pos

        car_clip = car_clip.set_position(make_position_func(car_y, stop_x))
        car_clips.append(car_clip)

    # Footer
    teaser, _ = make_text_image(
        next_race_text,
        fontsize=40,
        color="gray",
        font="ariali.ttf"
    )
    teaser = teaser.set_position(("center", HEIGHT - 60)).set_duration(DURATION)

    # Finish line (dashed)
    finish_y = bar_end_positions[-1][0] + BAR_HEIGHT + 30
    finish_line_clips = []
    for x in range(100, 700, 20):
        dash = ColorClip(size=(10, 4), color=(255, 255, 255)).set_duration(DURATION)
        dash = dash.set_position((x, finish_y))
        finish_line_clips.append(dash)

    # Flag on leader's bar
    leader_pos = standings_df.index.get_loc(top_index)
    leader_y, leader_bar_width = bar_end_positions[leader_pos]

    flag_img = Image.open(r"C:\F1_Project\assets\flag.png").convert("RGBA")
    orig_w, orig_h = flag_img.size
    new_h = 40
    new_w = int(orig_w * (new_h / orig_h))
    flag_img = flag_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    flag_clip = ImageClip(np.array(flag_img)).set_duration(DURATION)
    flag_clip = flag_clip.rotate(lambda t: t * 360)

    flag_x = 100 + leader_bar_width - new_w - 10
    flag_y = leader_y + (BAR_HEIGHT - new_h) // 2
    flag_clip = flag_clip.set_position((flag_x, flag_y))

    # Combine
    final = CompositeVideoClip(
        [bg, title, teaser] + bar_clips + car_clips + finish_line_clips + [flag_clip],
        size=(WIDTH, HEIGHT)
    )

    final.write_videofile(output_path, fps=25)