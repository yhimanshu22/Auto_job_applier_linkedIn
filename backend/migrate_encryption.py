import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_manager import db, SENSITIVE_KEYS

def migrate_sensitive_data():
    print("--- Migrating Sensitive Data to Encrypted Format ---")
    
    with db.conn:
        # Get all sensitive keys that are NOT yet encrypted
        rows = db.conn.execute(
            "SELECT key, value, category FROM configs WHERE key IN ({}) AND is_encrypted = 0".format(
                ','.join(['?'] * len(SENSITIVE_KEYS))
            ),
            SENSITIVE_KEYS
        ).fetchall()
        
        if not rows:
            print("No unencrypted sensitive data found.")
            return

        for row in rows:
            key = row["key"]
            value = row["value"] # This is still JSON stringified in the DB
            category = row["category"]
            
            print(f"Encrypting {key}...")
            # db.set_config will handle encryption automatically now
            import json
            db.set_config(key, json.loads(value), category)
            
    print("Migration complete.")

if __name__ == "__main__":
    migrate_sensitive_data()
