from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db_manager import db
from routes.config_parse import (
    format_config_content,
    normalize_stored_value,
    parse_config_content,
    parse_config_value,
)
from services.linkedin_env import migrate_canonical_linkedin_to_legacy
from utils.user_resolution import resolve_user_id

router = APIRouter(prefix="/api", tags=["config"])


class ConfigData(BaseModel):
    content: str


@router.get("/config/{category}")
async def read_config(category: str, request: Request, user_id: str | None = None):
    if category.endswith(".py"):
        category = category[:-3]

    if category not in ["personals", "search", "settings", "questions", "secrets"]:
        raise HTTPException(status_code=400, detail="Invalid config category")

    uid = await resolve_user_id(request, user_id)
    if category == "secrets":
        migrate_canonical_linkedin_to_legacy(user_id=uid)
    config_data = db.get_all_by_category(category, user_id=uid)
    if category == "search":
        config_data = {
            k: normalize_stored_value(k, v) for k, v in config_data.items()
        }

    content = format_config_content(category, config_data)

    return {"content": content}


@router.post("/config/{category}")
async def write_config(
    category: str, data: ConfigData, request: Request, user_id: str | None = None
):
    if category.endswith(".py"):
        category = category[:-3]

    if category not in ["personals", "search", "settings", "questions", "secrets"]:
        raise HTTPException(status_code=400, detail="Invalid config category")

    uid = await resolve_user_id(request, user_id)

    parsed = parse_config_content(data.content)
    for key, value in parsed.items():
        if category == "search":
            value = normalize_stored_value(key, value)
        db.set_config(key, value, category, user_id=uid)

    if category == "secrets":
        migrate_canonical_linkedin_to_legacy(user_id=uid)

    return {"status": "success"}
