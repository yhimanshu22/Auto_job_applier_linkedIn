import sqlite3
import json

conn = sqlite3.connect('data.db')
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT category, key, value FROM configs WHERE category='settings'")
for row in cursor:
    print(f"[{row['category']}] {row['key']} = {row['value']}")
conn.close()
