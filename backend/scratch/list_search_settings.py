import os
import sys
sys.path.append(os.getcwd())
from db_manager import db

print("Current search settings in DB:")
settings = db.get_all_by_category("search")
for k, v in settings.items():
    print(f"{k}: {v}")
