from sqlalchemy import Column, Integer, String, Text, DateTime, Float, LargeBinary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Config(Base):
    __tablename__ = "configs"
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
