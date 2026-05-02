import os
import sys
sys.path.append(os.getcwd())
from db_manager import db

print("Current settings in DB:")
settings = db.get_all_by_category("settings")
for k, v in settings.items():
    print(f"{k}: {v}")
