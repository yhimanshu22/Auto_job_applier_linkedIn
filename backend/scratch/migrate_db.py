import sqlite3
import os

db_path = os.path.join(os.getcwd(), "data.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Adding 'billing_cycle' column to 'subscriptions' table...")
    cursor.execute("ALTER TABLE subscriptions ADD COLUMN billing_cycle TEXT DEFAULT 'monthly'")
    conn.commit()
    print("Column added successfully.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column already exists.")
    else:
        print(f"Error: {e}")
finally:
    conn.close()
