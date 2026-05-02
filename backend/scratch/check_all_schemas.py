import sqlite3
import os

db_path = os.path.join(os.getcwd(), "data.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables = ["configs", "subscriptions", "bot_runs", "applications", "user_sessions", "assets", "resumes"]

for table in tables:
    print(f"\nSchema for '{table}' table:")
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
    except Exception as e:
        print(f"Error checking {table}: {e}")

conn.close()
