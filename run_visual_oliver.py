import json
import f1_visualizer_pro

with open("config_oliver.json") as f:
    cfg = json.load(f)

f1_visualizer_pro.run(cfg)