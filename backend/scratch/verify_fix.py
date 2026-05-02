import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to sys.path
sys.path.append(os.getcwd())
from models import Subscription

# Use data.db in current working directory (backend/)
db_path = os.path.join(os.getcwd(), "data.db")
db_url = f"sqlite:///{db_path}"

print(f"Connecting to: {db_url}")

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

session = SessionLocal()
try:
    sub = session.query(Subscription).first()
    print("Successfully queried subscriptions table.")
    if sub:
        print(f"Plan: {sub.plan}, Billing Cycle: {sub.billing_cycle}")
    else:
        print("No subscriptions found, but query succeeded.")
except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
