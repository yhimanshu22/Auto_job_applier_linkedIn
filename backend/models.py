from sqlalchemy import Column, Integer, String, Text, DateTime, Float, LargeBinary, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Config(Base):
    __tablename__ = "configs"
    # Multi-tenant: each user has their own config namespace.
    user_id = Column(String, primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(Text)
    category = Column(String)
    is_encrypted = Column(Integer, default=0)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True, nullable=False)
    stripe_customer_id = Column(String)
    stripe_subscription_id = Column(String)
    stripe_price_id = Column(String)
    plan = Column(String, default="free")
    billing_cycle = Column(String, default="monthly")
    status = Column(String, default="inactive")
    current_period_end = Column(String)
    cancel_at_period_end = Column(Integer, default=0)
    payment_provider = Column(String)  # stripe | payu
    payu_txnid = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BotRun(Base):
    __tablename__ = "bot_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    status = Column(String, default="running")
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    applications_count = Column(Integer, default=0)

    # `get_recent_bot_runs` orders by start_time DESC; this index turns the
    # otherwise full-table sort into an indexed reverse scan.
    __table_args__ = (
        Index("ix_bot_runs_start_time", "start_time"),
    )

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    job_title = Column(String)
    company = Column(String)
    location = Column(String)
    job_url = Column(String)
    status = Column(String, nullable=False) # 'applied', 'skipped', 'failed'
    reason = Column(Text)
    resume_used = Column(String)
    answer_generated = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # `(user_id, timestamp)` covers `get_recent_applications` and the
    # `get_application_stats` user filter.
    # `(user_id, status, timestamp)` covers `get_monthly_application_count`
    # (user + applied + 30d window) and `get_last_activity_snapshot` (user +
    # status ORDER BY timestamp).
    __table_args__ = (
        Index("ix_applications_user_timestamp", "user_id", "timestamp"),
        Index("ix_applications_user_status_ts", "user_id", "status", "timestamp"),
    )

class UserSession(Base):
    __tablename__ = "user_sessions"
    user_id = Column(String, primary_key=True)
    cookies_blob = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Asset(Base):
    __tablename__ = "assets"
    key = Column(String, primary_key=True)
    filename = Column(String)
    content = Column(LargeBinary)
    category = Column(String)

class ResumeMetadata(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False) # Local path or GS URL
    mime_type = Column(String, default="application/pdf")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AutomationTask(Base):
    """Persisted history of Linkedln-Automation-Framework subprocess runs.

    Mirrors the in-memory ``services.linkedin_automation.AutomationTask`` so the
    dashboard can surface task history (post / engage / pursue / calendar)
    across backend restarts.
    """
    __tablename__ = "automation_tasks"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    args_json = Column(Text)
    log_path = Column(String)
    status = Column(String, default="running")  # running | completed | failed | stopped
    exit_code = Column(Integer)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    # LinkedIn account the run authenticated as (email/username from env when
    # the subprocess starts). Useful for the dashboard so users with multiple
    # accounts can see which one each task touched.
    account_username = Column(String)

    # Hot read paths:
    #   - `(user_id, started_at)` → list_automation_tasks (ORDER BY started_at
    #     DESC), count_automation_tasks_today (started_at >= cutoff), and the
    #     user-scoped slices of get_automation_task_stats. SQLite scans the
    #     index in reverse for DESC, so one index covers both directions.
    #   - `(status,)` → get_automation_task_stats running-count query (no
    #     user_id), plus future "list-by-status" queries.
    __table_args__ = (
        Index("ix_automation_tasks_user_started", "user_id", "started_at"),
        Index("ix_automation_tasks_status", "status"),
    )


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    rating = Column(Integer)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommunityPost(Base):
    __tablename__ = "community_posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_name = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_community_posts_created", "created_at"),)


class CommunityReply(Base):
    __tablename__ = "community_replies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, nullable=False)
    parent_reply_id = Column(Integer)
    author_name = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_community_replies_post", "post_id", "created_at"),
    )
