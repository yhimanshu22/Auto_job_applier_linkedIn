import os
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, select, update, insert, func, case
from sqlalchemy.orm import sessionmaker, Session
from app_paths import get_runtime_writable_root
from models import Base, Config, Subscription, BotRun, Application, UserSession, Asset, ResumeMetadata
from utils.encryption import encrypt_data, decrypt_data

SENSITIVE_KEYS = [
    "llm_api_key",
    "openai_api_key",
    "password",
    "username",
    "linkedin_extra_accounts",  # JSON list of {username, password}
]


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
        # Database URL from environment variable, default to local SQLite
        # For GCP Cloud SQL, this would be: postgresql://user:pass@host:port/dbname
        self.db_url = os.getenv("DATABASE_URL")
        
        if not self.db_url:
            db_path = os.path.join(get_runtime_writable_root(), "data.db")
            self.db_url = f"sqlite:///{db_path}"
            
        # Create engine
        self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False} if "sqlite" in self.db_url else {})
        
        # Ensure all tables exist
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def set_config(self, key, value, category):
        is_encrypted = 1 if key in SENSITIVE_KEYS else 0
        val_str = json.dumps(value)
        
        if is_encrypted:
            val_str = encrypt_data(val_str)
            
        with self.get_session() as session:
            config = session.get(Config, key)
            if config:
                config.value = val_str
                config.category = category
                config.is_encrypted = is_encrypted
            else:
                config = Config(key=key, value=val_str, category=category, is_encrypted=is_encrypted)
                session.add(config)
            session.commit()

    def get_config(self, key, default=None):
        with self.get_session() as session:
            config = session.get(Config, key)
            if config:
                val_str = config.value
                if config.is_encrypted:
                    val_str = decrypt_data(val_str)
                return json.loads(val_str)
            return default

    def get_all_by_category(self, category):
        with self.get_session() as session:
            configs = session.query(Config).filter(Config.category == category).all()
            result = {}
            for config in configs:
                val_str = config.value
                if config.is_encrypted:
                    val_str = decrypt_data(val_str)
                result[config.key] = json.loads(val_str)
            return result

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

    def get_recent_bot_runs(self, limit=10):
        with self.get_session() as session:
            rows = (
                session.query(BotRun)
                .order_by(BotRun.start_time.desc())
                .limit(limit)
                .all()
            )
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
            if sess:
                decrypted_json = decrypt_data(sess.cookies_blob)
                return json.loads(decrypted_json)
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

    def close(self):
        # SQLAlchemy handles connections automatically via engine pooling
        pass

# Singleton instance
db = DatabaseManager()
