from fastapi import APIRouter, Request

from db_manager import db
from utils.user_resolution import resolve_user_id

router = APIRouter(tags=["applications"])


@router.get("/stats")
async def get_stats(request: Request, user_id: str | None = None):
    """Returns summary stats for a user's applications."""
    uid = await resolve_user_id(request, user_id)
    stats = db.get_application_stats(uid)
    # Add monthly count
    stats["monthly_count"] = db.get_monthly_application_count(uid)
    return stats


@router.get("/history")
async def get_history(request: Request, user_id: str | None = None, limit: int = 50):
    """Returns the most recent application attempts."""
    uid = await resolve_user_id(request, user_id)
    history = db.get_recent_applications(uid, limit)
    return {"history": history}


@router.get("/monthly-count")
async def get_monthly_count(request: Request, user_id: str | None = None):
    """Returns only the monthly application count."""
    uid = await resolve_user_id(request, user_id)
    count = db.get_monthly_application_count(uid)
    return {"count": count}
