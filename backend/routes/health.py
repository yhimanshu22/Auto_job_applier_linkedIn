from fastapi import APIRouter

from app_version import get_app_version

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "backend",
        "version": get_app_version(),
    }


@router.get("/version")
async def get_version():
    return {"version": get_app_version()}
