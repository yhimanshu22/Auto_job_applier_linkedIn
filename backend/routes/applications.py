from fastapi import APIRouter, HTTPException, Depends
from db_manager import db
from typing import List, Optional

router = APIRouter(tags=["applications"])

@router.get("/stats")
async def get_stats(user_id: str):
    """Returns summary stats for a user's applications."""
    stats = db.get_application_stats(user_id)
    # Add monthly count
    stats["monthly_count"] = db.get_monthly_application_count(user_id)
    return stats

@router.get("/history")
async def get_history(user_id: str, limit: int = 50):
    """Returns the most recent application attempts."""
    history = db.get_recent_applications(user_id, limit)
    return {"history": history}

@router.get("/monthly-count")
async def get_monthly_count(user_id: str):
    """Returns only the monthly application count."""
    count = db.get_monthly_application_count(user_id)
    return {"count": count}
