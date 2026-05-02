import os
import sys
sys.path.append(os.getcwd())
from db_manager import db

# Add bot_speed to settings if not exists
settings = db.get_all_by_category("settings")
if "bot_speed" not in settings:
    print("Adding bot_speed to settings...")
    db.set_config("bot_speed", 5, "settings")
else:
    print(f"bot_speed already exists: {settings['bot_speed']}")

# Also reduce click_gap for local-user if it's too high
if "click_gap" in settings and int(settings["click_gap"]) > 1:
    print("Reducing click_gap for faster processing...")
    db.set_config("click_gap", 1, "settings")
