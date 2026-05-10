from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "backend",
        "version": "1.1.0",
    }


@router.get("/version")
async def get_version():
    return {"version": "1.1.0"}
