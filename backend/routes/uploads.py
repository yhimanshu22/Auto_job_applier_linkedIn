from fastapi import APIRouter, File, HTTPException, UploadFile

from db_manager import db
from services.storage import storage_service

router = APIRouter(prefix="/api", tags=["uploads"])


@router.post("/upload/resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

    user_id = "local-user"

    try:
        content = await file.read()

        storage_path = storage_service.upload_file(content, file.filename, user_id)

        db.upsert_resume_metadata(user_id, file.filename, storage_path, is_default=True)

        db.set_config("default_resume_path", file.filename, "questions")

        return {"status": "success", "filename": file.filename, "storage_path": storage_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
