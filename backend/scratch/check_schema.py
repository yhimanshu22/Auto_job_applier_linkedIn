import sqlite3
import os

db_path = os.path.join(os.getcwd(), "data.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Schema for 'subscriptions' table:")
cursor.execute("PRAGMA table_info(subscriptions)")
columns = cursor.fetchall()
for col in columns:
    print(col)

conn.close()
