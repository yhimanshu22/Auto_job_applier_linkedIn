import os
import json
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, select, update, insert, func, case, literal, union_all
from sqlalchemy.orm import sessionmaker, Session
from app_paths import get_runtime_writable_root
from models import Base, Config, Subscription, BotRun, Application, UserSession, Asset, ResumeMetadata, AutomationTask, Feedback, CommunityPost, CommunityReply
from utils.encryption import encrypt_data, decrypt_data

SENSITIVE_KEYS = [
    "llm_api_key",
    "openai_api_key",
    "gemini_api_key",
    "grok_api_key",
    "groq_api_key",
    "LINKEDIN_PASSWORD",
]


def _is_sensitive_key(key: str) -> bool:
    if key in SENSITIVE_KEYS:
        return True
    return key.startswith("LINKEDIN_PASSWORD_")

# Legacy namespace used only when upgrading pre-multi-tenant DB schemas.
_LEGACY_MIGRATION_OWNER = "local-user"


def _ts_to_utc_iso(dt: datetime | None) -> str | None:
    """Serialize DB timestamps as RFC3339 UTC so browsers parse local time correctly."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # SQLite / drivers often return naive UTC
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    s = dt.isoformat()
    if s.endswith("+00:00"):
        return s[:-6] + "Z"
    return s


class DatabaseManager:
    def __init__(self):
        # Desktop sidecar: configs, secrets, applications, and bot history stay on
        # local SQLite under LINKDAPPLY_USER_DATA even if DATABASE_URL is set.
        force_local = os.getenv("LINKDAPPLY_LOCAL_DATA", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        self.db_url = None if force_local else os.getenv("DATABASE_URL")

        if self.db_url:
            # Render/Heroku use postgres://; SQLAlchemy expects postgresql://
            if self.db_url.startswith("postgres://"):
                self.db_url = self.db_url.replace(
                    "postgres://", "postgresql://", 1
                )

        if not self.db_url:
            db_path = os.path.join(get_runtime_writable_root(), "data.db")
            self.db_url = f"sqlite:///{db_path}"
            
        # Create engine
        self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False} if "sqlite" in self.db_url else {})
        
        # Ensure all tables exist
        Base.metadata.create_all(self.engine)
        # Add columns that are new since this DB file was first created.
        # ``create_all`` only creates missing tables/indexes — never columns.
        self._migrate_runtime_columns()

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _migrate_runtime_columns(self):
        """Best-effort additive schema migration (no Alembic for two changes).

        Handles:
          * ``automation_tasks.account_username`` (SQLite-only legacy add).
          * ``configs.user_id`` — multi-tenant config namespace. Existing rows
            are assigned to the legacy owner id and the primary key becomes
            ``(user_id, key)``. Implemented for both SQLite and Postgres.
        """
        try:
            with self.engine.begin() as conn:
                if "sqlite" in self.db_url:
                    self._sqlite_migrations(conn)
                elif self.db_url.startswith("postgresql"):
                    self._postgres_migrations(conn)
        except Exception as exc:
            import logging
            logging.warning(f"Runtime schema migration skipped: {exc}")

    @staticmethod
    def _sqlite_migrations(conn):
        # automation_tasks.account_username (additive)
        cols = {
            row[1]
            for row in conn.exec_driver_sql(
                "PRAGMA table_info(automation_tasks)"
            ).fetchall()
        }
        if cols and "account_username" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE automation_tasks ADD COLUMN account_username TEXT"
            )

        sub_cols = {
            row[1]
            for row in conn.exec_driver_sql(
                "PRAGMA table_info(subscriptions)"
            ).fetchall()
        }
        if sub_cols:
            if "payment_provider" not in sub_cols:
                conn.exec_driver_sql(
                    "ALTER TABLE subscriptions ADD COLUMN payment_provider TEXT"
                )
            if "payu_txnid" not in sub_cols:
                conn.exec_driver_sql(
                    "ALTER TABLE subscriptions ADD COLUMN payu_txnid TEXT"
                )

        # configs.user_id — SQLite can't alter a PK, so rebuild the table.
        cols = {
            row[1]
            for row in conn.exec_driver_sql("PRAGMA table_info(configs)").fetchall()
        }
        if cols and "user_id" not in cols:
            conn.exec_driver_sql(
                "CREATE TABLE configs_new ("
                f"user_id TEXT NOT NULL DEFAULT '{_LEGACY_MIGRATION_OWNER}', "
                "key TEXT NOT NULL, "
                "value TEXT, category TEXT, is_encrypted INTEGER DEFAULT 0, "
                "PRIMARY KEY (user_id, key))"
            )
            conn.exec_driver_sql(
                "INSERT INTO configs_new (user_id, key, value, category, is_encrypted) "
                f"SELECT '{_LEGACY_MIGRATION_OWNER}', key, value, category, is_encrypted FROM configs"
            )
            conn.exec_driver_sql("DROP TABLE configs")
            conn.exec_driver_sql("ALTER TABLE configs_new RENAME TO configs")

        DatabaseManager._migrate_community_tables(conn, dialect="sqlite")

    @staticmethod
    def _migrate_community_tables(conn, *, dialect: str) -> None:
        """Rebuild community tables when legacy columns (title, email, etc.) are present."""
        if dialect == "sqlite":
            post_cols = {
                row[1]
                for row in conn.exec_driver_sql(
                    "PRAGMA table_info(community_posts)"
                ).fetchall()
            }
            if post_cols and ("author_email" in post_cols or "title" in post_cols):
                conn.exec_driver_sql(
                    "CREATE TABLE community_posts_new ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "author_name TEXT NOT NULL, "
                    "body TEXT NOT NULL, "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
                )
                conn.exec_driver_sql(
                    "INSERT INTO community_posts_new (id, author_name, body, created_at) "
                    "SELECT id, author_name, body, created_at FROM community_posts"
                )
                conn.exec_driver_sql("DROP TABLE community_posts")
                conn.exec_driver_sql(
                    "ALTER TABLE community_posts_new RENAME TO community_posts"
                )
                conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_community_posts_created "
                    "ON community_posts (created_at)"
                )

            reply_cols = {
                row[1]
                for row in conn.exec_driver_sql(
                    "PRAGMA table_info(community_replies)"
                ).fetchall()
            }
            if reply_cols and "author_email" in reply_cols:
                conn.exec_driver_sql(
                    "CREATE TABLE community_replies_new ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "post_id INTEGER NOT NULL, "
                    "parent_reply_id INTEGER, "
                    "author_name TEXT NOT NULL, "
                    "body TEXT NOT NULL, "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
                )
                conn.exec_driver_sql(
                    "INSERT INTO community_replies_new "
                    "(id, post_id, parent_reply_id, author_name, body, created_at) "
                    "SELECT id, post_id, parent_reply_id, author_name, body, created_at "
                    "FROM community_replies"
                )
                conn.exec_driver_sql("DROP TABLE community_replies")
                conn.exec_driver_sql(
                    "ALTER TABLE community_replies_new RENAME TO community_replies"
                )
                conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_community_replies_post "
                    "ON community_replies (post_id, created_at)"
                )
            return

        post_cols = {
            r[0]
            for r in conn.exec_driver_sql(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'community_posts'"
            ).fetchall()
        }
        if post_cols and ("author_email" in post_cols or "title" in post_cols):
            conn.exec_driver_sql(
                "CREATE TABLE community_posts_new ("
                "id SERIAL PRIMARY KEY, "
                "author_name VARCHAR NOT NULL, "
                "body TEXT NOT NULL, "
                "created_at TIMESTAMPTZ DEFAULT NOW())"
            )
            conn.exec_driver_sql(
                "INSERT INTO community_posts_new (id, author_name, body, created_at) "
                "SELECT id, author_name, body, created_at FROM community_posts"
            )
            conn.exec_driver_sql("DROP TABLE community_posts CASCADE")
            conn.exec_driver_sql(
                "ALTER TABLE community_posts_new RENAME TO community_posts"
            )
            conn.exec_driver_sql(
                "CREATE INDEX ix_community_posts_created ON community_posts (created_at)"
            )
            conn.exec_driver_sql(
                "SELECT setval(pg_get_serial_sequence('community_posts', 'id'), "
                "COALESCE((SELECT MAX(id) FROM community_posts), 1))"
            )

        reply_cols = {
            r[0]
            for r in conn.exec_driver_sql(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'community_replies'"
            ).fetchall()
        }
        if reply_cols and "author_email" in reply_cols:
            conn.exec_driver_sql(
                "CREATE TABLE community_replies_new ("
                "id SERIAL PRIMARY KEY, "
                "post_id INTEGER NOT NULL, "
                "parent_reply_id INTEGER, "
                "author_name VARCHAR NOT NULL, "
                "body TEXT NOT NULL, "
                "created_at TIMESTAMPTZ DEFAULT NOW())"
            )
            conn.exec_driver_sql(
                "INSERT INTO community_replies_new "
                "(id, post_id, parent_reply_id, author_name, body, created_at) "
                "SELECT id, post_id, parent_reply_id, author_name, body, created_at "
                "FROM community_replies"
            )
            conn.exec_driver_sql("DROP TABLE community_replies")
            conn.exec_driver_sql(
                "ALTER TABLE community_replies_new RENAME TO community_replies"
            )
            conn.exec_driver_sql(
                "CREATE INDEX ix_community_replies_post "
                "ON community_replies (post_id, created_at)"
            )
            conn.exec_driver_sql(
                "SELECT setval(pg_get_serial_sequence('community_replies', 'id'), "
                "COALESCE((SELECT MAX(id) FROM community_replies), 1))"
            )

    @staticmethod
    def _postgres_migrations(conn):
        sub_cols = {
            r[0]
            for r in conn.exec_driver_sql(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'subscriptions'"
            ).fetchall()
        }
        if sub_cols:
            if "payment_provider" not in sub_cols:
                conn.exec_driver_sql(
                    "ALTER TABLE subscriptions ADD COLUMN payment_provider VARCHAR"
                )
            if "payu_txnid" not in sub_cols:
                conn.exec_driver_sql(
                    "ALTER TABLE subscriptions ADD COLUMN payu_txnid VARCHAR"
                )

        cols = {
            r[0]
            for r in conn.exec_driver_sql(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'configs'"
            ).fetchall()
        }
        if cols and "user_id" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE configs ADD COLUMN user_id VARCHAR NOT NULL "
                f"DEFAULT '{_LEGACY_MIGRATION_OWNER}'"
            )
            conn.exec_driver_sql("ALTER TABLE configs DROP CONSTRAINT configs_pkey")
            conn.exec_driver_sql("ALTER TABLE configs ADD PRIMARY KEY (user_id, key)")

        DatabaseManager._migrate_community_tables(conn, dialect="postgres")

    def get_session(self) -> Session:
        return self.SessionLocal()

    def set_config(self, key, value, category, *, user_id: str):
        is_encrypted = 1 if _is_sensitive_key(key) else 0
        val_str = json.dumps(value)
        
        if is_encrypted:
            val_str = encrypt_data(val_str)
            
        with self.get_session() as session:
            config = session.get(Config, (user_id, key))
            if config:
                config.value = val_str
                config.category = category
                config.is_encrypted = is_encrypted
            else:
                config = Config(user_id=user_id, key=key, value=val_str, category=category, is_encrypted=is_encrypted)
                session.add(config)
            session.commit()

    def delete_config(self, key, category=None, *, user_id: str):
        """Remove a config row outright (no-op if it doesn't exist).

        Used by the LinkedIn automation form-defaults clear flow — writing
        ``None`` via :meth:`set_config` would still leave a row that surfaces
        as a key (with a null value) in ``get_all_by_category``. Deleting
        keeps the listing clean and the ETag stable across set/clear cycles.

        When ``category`` is given the delete only matches that category,
        which prevents an accidental cross-category wipe if two categories
        share a key name in the future.
        """
        with self.get_session() as session:
            q = session.query(Config).filter(
                Config.key == key, Config.user_id == user_id
            )
            if category is not None:
                q = q.filter(Config.category == category)
            row = q.first()
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    @staticmethod
    def _decode_config(config):
        val_str = config.value
        if val_str is None or (isinstance(val_str, str) and not val_str.strip()):
            return None
        if config.is_encrypted:
            val_str = decrypt_data(val_str)
            if val_str is None or (isinstance(val_str, str) and not val_str.strip()):
                return None
        try:
            return json.loads(val_str)
        except json.JSONDecodeError:
            if config.is_encrypted:
                logging.warning(
                    "Could not decode encrypted config for %s/%s (%s)",
                    config.user_id,
                    config.key,
                    config.category,
                )
                return None
            logging.warning(
                "Skipping invalid config JSON for %s/%s (%s)",
                config.user_id,
                config.key,
                config.category,
            )
            return None

    def get_config(self, key, default=None, *, user_id: str):
        with self.get_session() as session:
            config = session.get(Config, (user_id, key))
            if config:
                return self._decode_config(config)
            return default

    def get_all_by_category(self, category, *, user_id: str):
        with self.get_session() as session:
            result = {}
            configs = session.query(Config).filter(
                Config.category == category, Config.user_id == user_id
            ).all()
            for config in configs:
                decoded = self._decode_config(config)
                if decoded is not None:
                    result[config.key] = decoded
            return result

    def list_config_user_ids(self, category: str, key: str) -> list[str]:
        """Distinct user_ids that have ``key`` stored under ``category``."""
        with self.get_session() as session:
            rows = (
                session.query(Config.user_id)
                .filter(Config.category == category, Config.key == key)
                .distinct()
                .all()
            )
            return [r[0] for r in rows if r and r[0]]

    def upsert_subscription(self, user_id, **kwargs):
        with self.get_session() as session:
            sub = session.query(Subscription).filter(Subscription.user_id == user_id).first()
            if sub:
                for k, v in kwargs.items():
                    setattr(sub, k, v)
            else:
                sub = Subscription(user_id=user_id, **kwargs)
                session.add(sub)
            session.commit()

    def get_user_subscription(self, user_id):
        with self.get_session() as session:
            sub = session.query(Subscription).filter(Subscription.user_id == user_id).first()
            if sub:
                # Convert to dict for compatibility
                return {c.name: getattr(sub, c.name) for c in sub.__table__.columns}
            return None

    def start_bot_run(self, user_id):
        with self.get_session() as session:
            run = BotRun(user_id=user_id, status='running')
            session.add(run)
            session.commit()
            session.refresh(run)
            return run.id

    def end_bot_run(self, run_id, count=0):
        with self.get_session() as session:
            run = session.get(BotRun, run_id)
            if run:
                run.status = 'completed'
                run.end_time = func.now()
                run.applications_count = count
                session.commit()

    def get_recent_bot_runs(self, limit=10, user_id=None):
        with self.get_session() as session:
            q = session.query(BotRun)
            if user_id:
                q = q.filter(BotRun.user_id == user_id)
            rows = q.order_by(BotRun.start_time.desc()).limit(limit).all()
            return [
                {c.name: getattr(run, c.name) for c in run.__table__.columns}
                for run in rows
            ]

    def log_application(self, user_id, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.now(timezone.utc)
        with self.get_session() as session:
            app = Application(user_id=user_id, **kwargs)
            session.add(app)
            session.commit()

    def get_monthly_application_count(self, user_id):
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        with self.get_session() as session:
            count = session.query(func.count(Application.id)).filter(
                Application.user_id == user_id,
                Application.status == 'applied',
                Application.timestamp >= thirty_days_ago
            ).scalar()
            return count or 0

    def get_application_stats(self, user_id):
        with self.get_session() as session:
            stats = session.query(
                func.count(Application.id).label('total'),
                func.sum(case((Application.status == 'applied', 1), else_=0)).label('applied'),
                func.sum(case((Application.status == 'skipped', 1), else_=0)).label('skipped'),
                func.sum(case((Application.status == 'failed', 1), else_=0)).label('failed')
            ).filter(Application.user_id == user_id).first()
            
            return {
                "total": stats.total or 0,
                "applied": int(stats.applied or 0),
                "skipped": int(stats.skipped or 0),
                "failed": int(stats.failed or 0)
            }

    def get_recent_applications(self, user_id, limit=20):
        with self.get_session() as session:
            apps = session.query(Application).filter(
                Application.user_id == user_id
            ).order_by(Application.timestamp.desc()).limit(limit).all()

            rows = []
            for app in apps:
                d = {c.name: getattr(app, c.name) for c in app.__table__.columns}
                d["timestamp"] = _ts_to_utc_iso(d.get("timestamp"))
                rows.append(d)
            return rows

    def get_last_activity_snapshot(self, user_id: str):
        """Latest successful apply and latest failure for the dashboard home story."""
        with self.get_session() as session:
            applied = (
                session.query(Application)
                .filter(Application.user_id == user_id, Application.status == "applied")
                .order_by(Application.timestamp.desc())
                .first()
            )
            failed = (
                session.query(Application)
                .filter(Application.user_id == user_id, Application.status == "failed")
                .order_by(Application.timestamp.desc())
                .first()
            )

        def pack(app):
            if not app:
                return None
            return {
                "company": app.company,
                "job_title": app.job_title,
                "job_url": app.job_url,
                "timestamp": _ts_to_utc_iso(app.timestamp),
                "reason": app.reason,
                "status": app.status,
            }

        return {"last_applied": pack(applied), "last_failed": pack(failed)}

    def set_user_session(self, user_id, cookies_dict):
        cookies_json = json.dumps(cookies_dict)
        encrypted_cookies = encrypt_data(cookies_json)
        with self.get_session() as session:
            sess = session.get(UserSession, user_id)
            if sess:
                sess.cookies_blob = encrypted_cookies
                sess.updated_at = func.now()
            else:
                sess = UserSession(user_id=user_id, cookies_blob=encrypted_cookies)
                session.add(sess)
            session.commit()

    def get_user_session(self, user_id):
        with self.get_session() as session:
            sess = session.get(UserSession, user_id)
            if not sess or not sess.cookies_blob:
                return None
            try:
                decrypted_json = decrypt_data(sess.cookies_blob)
                if not decrypted_json or not str(decrypted_json).strip():
                    return None
                return json.loads(decrypted_json)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                logging.warning("Could not decode session cookies for %s: %s", user_id, exc)
                return None

    def upsert_resume_metadata(self, user_id, file_name, storage_path, is_default=False):
        """Stores resume metadata in the database."""
        with self.get_session() as session:
            # If setting as default, unset others
            if is_default:
                session.query(ResumeMetadata).filter(
                    ResumeMetadata.user_id == user_id
                ).update({ResumeMetadata.is_default: False})
            
            # Check if this file already exists for this user
            resume = session.query(ResumeMetadata).filter(
                ResumeMetadata.user_id == user_id,
                ResumeMetadata.file_name == file_name
            ).first()
            
            if resume:
                resume.storage_path = storage_path
                resume.is_default = is_default
            else:
                resume = ResumeMetadata(
                    user_id=user_id,
                    file_name=file_name,
                    storage_path=storage_path,
                    is_default=is_default
                )
                session.add(resume)
            session.commit()
            return resume.id

    def get_user_resumes(self, user_id):
        """Retrieves all resumes for a user."""
        with self.get_session() as session:
            resumes = session.query(ResumeMetadata).filter(
                ResumeMetadata.user_id == user_id
            ).all()
            return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in resumes]

    def set_default_resume(self, user_id, resume_id):
        """Sets a specific resume as the default for a user."""
        with self.get_session() as session:
            # Unset all
            session.query(ResumeMetadata).filter(
                ResumeMetadata.user_id == user_id
            ).update({ResumeMetadata.is_default: False})
            
            # Set target
            resume = session.get(ResumeMetadata, resume_id)
            if resume and resume.user_id == user_id:
                resume.is_default = True
                session.commit()
                return True
            return False

    def set_asset(self, key, filename, content, category):
        with self.get_session() as session:
            asset = session.get(Asset, key)
            if asset:
                asset.filename = filename
                asset.content = content
                asset.category = category
            else:
                asset = Asset(key=key, filename=filename, content=content, category=category)
                session.add(asset)
            session.commit()

    def get_asset(self, key):
        with self.get_session() as session:
            asset = session.get(Asset, key)
            if asset:
                return {"filename": asset.filename, "content": asset.content}
            return None

    # ------------------------------------------------------------------
    # LinkedIn Automation Framework task history
    # ------------------------------------------------------------------

    def reconcile_stale_automation_tasks(self, max_age_minutes: int | None = None) -> int:
        """Mark ``running`` tasks with no ``ended_at`` as interrupted if they are too old.

        When the API process restarts or ``finalize_automation_task`` fails, rows can
        stay ``status='running'`` forever — the dashboard then shows bots active when
        nothing is running. This is a cheap periodic repair (see env
        ``LINKEDIN_STALE_TASK_MINUTES``, default 30).
        """
        if max_age_minutes is None:
            try:
                max_age_minutes = int(os.getenv("LINKEDIN_STALE_TASK_MINUTES", "30"))
            except ValueError:
                max_age_minutes = 30
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        now = datetime.now(timezone.utc)
        with self.get_session() as session:
            result = session.execute(
                update(AutomationTask)
                .where(
                    AutomationTask.status == "running",
                    AutomationTask.ended_at.is_(None),
                    AutomationTask.started_at < cutoff,
                )
                .values(
                    status="interrupted",
                    exit_code=-9,
                    ended_at=now,
                )
            )
            session.commit()
            return int(result.rowcount or 0)

    def create_automation_task(
        self,
        task_id,
        action,
        args,
        log_path,
        user_id: str,
        account_username=None,
    ):
        """Persist a freshly-launched LinkedIn automation subprocess."""
        with self.get_session() as session:
            row = AutomationTask(
                id=task_id,
                user_id=user_id,
                action=action,
                args_json=json.dumps(args or []),
                log_path=log_path,
                status="running",
                account_username=account_username,
            )
            session.add(row)
            session.commit()

    def finalize_automation_task(self, task_id, exit_code, status=None):
        """Record exit code / status when the subprocess ends or is stopped."""
        with self.get_session() as session:
            row = session.get(AutomationTask, task_id)
            if not row:
                return
            row.exit_code = int(exit_code) if exit_code is not None else None
            row.ended_at = datetime.now(timezone.utc)
            if status:
                row.status = status
            else:
                row.status = "completed" if exit_code == 0 else "failed"
            session.commit()

    def get_automation_task(self, task_id):
        with self.get_session() as session:
            row = session.get(AutomationTask, task_id)
            if not row:
                return None
            return self._automation_task_to_dict(row)

    def list_automation_tasks(self, limit=50, user_id=None):
        self.reconcile_stale_automation_tasks()
        with self.get_session() as session:
            q = session.query(AutomationTask)
            if user_id:
                q = q.filter(AutomationTask.user_id == user_id)
            rows = q.order_by(AutomationTask.started_at.desc()).limit(limit).all()
            return [self._automation_task_to_dict(r) for r in rows]

    def count_automation_tasks_today(self, user_id):
        """Number of automation tasks started in the last 24 hours for a user."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        with self.get_session() as session:
            count = (
                session.query(func.count(AutomationTask.id))
                .filter(
                    AutomationTask.user_id == user_id,
                    AutomationTask.started_at >= cutoff,
                )
                .scalar()
            )
            return int(count or 0)

    def get_automation_task_stats(self, user_id=None):
        """Aggregate automation task counts for the dashboard panel.

        Hot path — the dashboard polls this every ~5s. Previously emitted 6
        separate SELECTs (4 scalar counts + 2 GROUP BYs). Now collapsed into
        **2 queries**:

          1. Single SELECT with 4 ``CASE WHEN`` aggregates (total / 24h / 30d /
             running) — one index scan over the user's rows.
          2. One SELECT with ``UNION ALL`` over two GROUP BYs (by action +
             by status, both 30d-windowed) — one network roundtrip.

        Returns counts windowed by 24h / 30d / all-time, plus per-action and
        per-status breakdowns over the last 30 days.
        """
        now = datetime.now(timezone.utc)
        day_cutoff = now - timedelta(hours=24)
        month_cutoff = now - timedelta(days=30)

        self.reconcile_stale_automation_tasks()

        # Common WHERE clause(s) — applied to both queries so the user_id
        # filter (or lack thereof) stays consistent.
        user_filter = (
            [AutomationTask.user_id == user_id] if user_id else []
        )

        with self.get_session() as session:
            # ---- Query 1: 4 aggregates in a single index scan ----
            counts_row = (
                session.query(
                    func.count(AutomationTask.id).label("total_all"),
                    func.sum(
                        case((AutomationTask.started_at >= day_cutoff, 1), else_=0)
                    ).label("total_day"),
                    func.sum(
                        case((AutomationTask.started_at >= month_cutoff, 1), else_=0)
                    ).label("total_month"),
                    func.sum(
                        case((AutomationTask.status == "running", 1), else_=0)
                    ).label("running"),
                )
                .filter(*user_filter)
                .one()
            )

            # ---- Query 2: per-action + per-status breakdown via UNION ALL ----
            action_q = (
                session.query(
                    literal("action").label("kind"),
                    AutomationTask.action.label("key"),
                    func.count(AutomationTask.id).label("cnt"),
                )
                .filter(AutomationTask.started_at >= month_cutoff, *user_filter)
                .group_by(AutomationTask.action)
            )
            status_q = (
                session.query(
                    literal("status").label("kind"),
                    AutomationTask.status.label("key"),
                    func.count(AutomationTask.id).label("cnt"),
                )
                .filter(AutomationTask.started_at >= month_cutoff, *user_filter)
                .group_by(AutomationTask.status)
            )
            breakdown_rows = action_q.union_all(status_q).all()

        by_action: dict = {}
        by_status: dict = {}
        for kind, key, cnt in breakdown_rows:
            if kind == "action":
                by_action[key] = int(cnt)
            else:
                by_status[key] = int(cnt)

        return {
            "total_all_time": int(counts_row.total_all or 0),
            "last_24h": int(counts_row.total_day or 0),
            "last_30d": int(counts_row.total_month or 0),
            "running": int(counts_row.running or 0),
            "by_action_30d": by_action,
            "by_status_30d": by_status,
        }

    @staticmethod
    def _automation_task_to_dict(row):
        try:
            args = json.loads(row.args_json) if row.args_json else []
        except Exception:
            args = []
        return {
            "id": row.id,
            "user_id": row.user_id,
            "action": row.action,
            "args": args,
            "log_path": row.log_path,
            "status": row.status,
            "exit_code": row.exit_code,
            "started_at": _ts_to_utc_iso(row.started_at),
            "ended_at": _ts_to_utc_iso(row.ended_at),
            "account_username": row.account_username,
        }

    def create_feedback(
        self,
        *,
        name: str,
        email: str,
        message: str,
        rating: int | None = None,
    ) -> dict:
        with self.SessionLocal() as session:
            row = Feedback(
                name=name,
                email=email,
                message=message,
                rating=rating,
                published=False,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return {
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "message": row.message,
                "rating": row.rating,
                "published": bool(row.published),
                "created_at": _ts_to_utc_iso(row.created_at),
            }

    def ensure_community_seeded(self) -> None:
        from data.community_seed import COMMUNITY_SEED_THREADS

        with self.SessionLocal() as session:
            if session.query(CommunityPost).count() > 0:
                return

            for thread in COMMUNITY_SEED_THREADS:
                post = CommunityPost(
                    author_name=thread["author_name"],
                    body=thread["body"],
                )
                session.add(post)
                session.flush()

                reply_ids: list[int] = []
                for reply_data in thread.get("replies", []):
                    parent_idx = reply_data.get("parent_index")
                    parent_id = (
                        reply_ids[parent_idx]
                        if parent_idx is not None and parent_idx < len(reply_ids)
                        else None
                    )
                    reply = CommunityReply(
                        post_id=post.id,
                        parent_reply_id=parent_id,
                        author_name=reply_data["author_name"],
                        body=reply_data["body"],
                    )
                    session.add(reply)
                    session.flush()
                    reply_ids.append(reply.id)

            session.commit()

    @staticmethod
    def _community_reply_to_dict(row: CommunityReply) -> dict:
        return {
            "id": row.id,
            "post_id": row.post_id,
            "parent_reply_id": row.parent_reply_id,
            "author_name": row.author_name,
            "body": row.body,
            "created_at": _ts_to_utc_iso(row.created_at),
        }

    @staticmethod
    def _community_post_to_dict(row: CommunityPost, replies: list[dict]) -> dict:
        return {
            "id": row.id,
            "author_name": row.author_name,
            "body": row.body,
            "reply_count": len(replies),
            "created_at": _ts_to_utc_iso(row.created_at),
            "replies": replies,
        }

    def list_community_posts(self, *, limit: int = 50) -> list[dict]:
        with self.SessionLocal() as session:
            posts = (
                session.query(CommunityPost)
                .order_by(CommunityPost.created_at.desc())
                .limit(limit)
                .all()
            )
            result = []
            for post in posts:
                replies = (
                    session.query(CommunityReply)
                    .filter(CommunityReply.post_id == post.id)
                    .order_by(CommunityReply.created_at.asc())
                    .all()
                )
                result.append(
                    self._community_post_to_dict(
                        post,
                        [self._community_reply_to_dict(r) for r in replies],
                    )
                )
            return result

    def get_community_post(self, post_id: int) -> dict | None:
        with self.SessionLocal() as session:
            post = session.get(CommunityPost, post_id)
            if not post:
                return None
            replies = (
                session.query(CommunityReply)
                .filter(CommunityReply.post_id == post_id)
                .order_by(CommunityReply.created_at.asc())
                .all()
            )
            return self._community_post_to_dict(
                post,
                [self._community_reply_to_dict(r) for r in replies],
            )

    def create_community_post(
        self,
        *,
        author_name: str,
        body: str,
    ) -> dict:
        with self.SessionLocal() as session:
            row = CommunityPost(
                author_name=author_name,
                body=body,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._community_post_to_dict(row, [])

    def create_community_reply(
        self,
        *,
        post_id: int,
        author_name: str,
        body: str,
        parent_reply_id: int | None = None,
    ) -> dict:
        with self.SessionLocal() as session:
            post = session.get(CommunityPost, post_id)
            if not post:
                raise ValueError("Post not found")

            if parent_reply_id is not None:
                parent = session.get(CommunityReply, parent_reply_id)
                if not parent or parent.post_id != post_id:
                    raise ValueError("Invalid parent reply")

            row = CommunityReply(
                post_id=post_id,
                parent_reply_id=parent_reply_id,
                author_name=author_name,
                body=body,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._community_reply_to_dict(row)

    def close(self):
        # SQLAlchemy handles connections automatically via engine pooling
        pass

# Singleton instance
db = DatabaseManager()
