from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from db_manager import db
from services.storage import storage_service
from utils.user_resolution import resolve_user_id

router = APIRouter(prefix="/api", tags=["uploads"])


@router.post("/upload/resume")
async def upload_resume(
    request: Request, file: UploadFile = File(...), user_id: str | None = None
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

    uid = await resolve_user_id(request, user_id)

    try:
        content = await file.read()

        storage_path = storage_service.upload_file(content, file.filename, uid)

        db.upsert_resume_metadata(uid, file.filename, storage_path, is_default=True)

        db.set_config("default_resume_path", storage_path, "questions", user_id=uid)

        return {"status": "success", "filename": file.filename, "storage_path": storage_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
