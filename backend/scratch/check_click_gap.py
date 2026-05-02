import os
import sys
sys.path.append(os.getcwd())
from db_manager import db
from sqlalchemy import text

with db.engine.connect() as conn:
    result = conn.execute(text("SELECT key, value, category FROM configs WHERE key = 'click_gap'"))
    row = result.fetchone()
    if row:
        print(f"Found: {row}")
    else:
        print("Not found in DB")
