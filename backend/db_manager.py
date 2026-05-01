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
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                stripe_price_id TEXT,
                plan TEXT DEFAULT 'free',
                status TEXT DEFAULT 'inactive',
                current_period_end TEXT,
                cancel_at_period_end INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                applications_count INTEGER DEFAULT 0
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
        
    def upsert_subscription(self, user_id, **kwargs):
        """Upsert a subscription record for a given user."""
        # First check if the user exists
        row = self.conn.execute("SELECT id FROM subscriptions WHERE user_id = ?", (user_id,)).fetchone()
        
        if not row:
            # Insert default with kwargs overrides
            fields = ['user_id'] + list(kwargs.keys())
            placeholders = ', '.join(['?'] * len(fields))
            values = [user_id] + list(kwargs.values())
            query = f"INSERT INTO subscriptions ({', '.join(fields)}) VALUES ({placeholders})"
            self.conn.execute(query, values)
        else:
            # Update
            kwargs['updated_at'] = 'CURRENT_TIMESTAMP'
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            # For CURRENT_TIMESTAMP we should technically not use ? if we want the DB to evaluate it,
            # but since we're using SQLite, we can just pass the string or use datetime.
            # Let's clean that up to use actual SQLite functions
            
            clean_kwargs = {k: v for k, v in kwargs.items() if k != 'updated_at'}
            set_clause = ', '.join([f"{k} = ?" for k in clean_kwargs.keys()]) + ", updated_at = CURRENT_TIMESTAMP"
            
            query = f"UPDATE subscriptions SET {set_clause} WHERE user_id = ?"
            values = list(clean_kwargs.values()) + [user_id]
            self.conn.execute(query, values)
            
        self.conn.commit()

    def get_user_subscription(self, user_id):
        """Retrieves subscription details for a user."""
        row = self.conn.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return dict(row)
        return None

    def start_bot_run(self, user_id):
        """Creates a new bot run record and returns its ID."""
        cursor = self.conn.execute(
            "INSERT INTO bot_runs (user_id, status) VALUES (?, 'running')",
            (user_id,)
        )
        self.conn.commit()
        return cursor.lastrowid

    def end_bot_run(self, run_id, count=0):
        """Marks a bot run as completed."""
        self.conn.execute(
            "UPDATE bot_runs SET status = 'completed', end_time = CURRENT_TIMESTAMP, applications_count = ? WHERE id = ?",
            (count, run_id)
        )
        self.conn.commit()

    def get_recent_bot_runs(self, limit=10):
        """Retrieves recent bot run history."""
        rows = self.conn.execute(
            "SELECT * FROM bot_runs ORDER BY start_time DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self):
        self.conn.close()

# Singleton instance
db = DatabaseManager()
