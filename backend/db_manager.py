import sqlite3
import json
import os

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, "data.db")
        else:
            self.db_path = db_path
            
        # Ensure directory exists
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS configs (
                key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                key TEXT PRIMARY KEY,
                filename TEXT,
                content BLOB,
                category TEXT
            )
        """)
        self.conn.commit()

    def set_config(self, key, value, category):
        # Convert values to JSON for database storage
        val_json = json.dumps(value)
        self.conn.execute(
            "INSERT OR REPLACE INTO configs (key, value, category) VALUES (?, ?, ?)", 
            (key, val_json, category)
        )
        self.conn.commit()

    def set_asset(self, key, filename, content, category):
        """Stores a binary asset (e.g., PDF) as a BLOB."""
        self.conn.execute(
            "INSERT OR REPLACE INTO assets (key, filename, content, category) VALUES (?, ?, ?, ?)",
            (key, filename, content, category)
        )
        self.conn.commit()

    def get_asset(self, key):
        """Retrieves a binary asset and its metadata."""
        row = self.conn.execute("SELECT filename, content FROM assets WHERE key = ?", (key,)).fetchone()
        if row:
            return {"filename": row["filename"], "content": row["content"]}
        return None

    def get_config(self, key, default=None):
        row = self.conn.execute("SELECT value FROM configs WHERE key = ?", (key,)).fetchone()
        if row:
            return json.loads(row["value"])
        return default

    def get_all_by_category(self, category):
        rows = self.conn.execute("SELECT key, value FROM configs WHERE category = ?", (category,)).fetchall()
        return {row["key"]: json.loads(row["value"]) for row in rows}

    def close(self):
        self.conn.close()

# Singleton instance
db = DatabaseManager()
