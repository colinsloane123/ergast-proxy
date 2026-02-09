import json
from scoring_engine import update_standings

with open("config_main.json") as f:
    cfg = json.load(f)

update_standings(cfg["spreadsheet_id"], cfg["credentials_file"])