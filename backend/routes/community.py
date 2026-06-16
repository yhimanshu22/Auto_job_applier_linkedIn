from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db_manager import db
from services.email import send_community_notification

router = APIRouter(prefix="/api/community", tags=["community"])


class PostCreate(BaseModel):
    author_name: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=10, max_length=4000)


class ReplyCreate(BaseModel):
    author_name: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=2, max_length=2000)
    parent_reply_id: int | None = None


@router.get("/posts")
async def list_posts(limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(limit, 100))
    db.ensure_community_seeded()
    posts = db.list_community_posts(limit=limit)
    return {"posts": posts}


@router.get("/posts/{post_id}")
async def get_post(post_id: int) -> dict[str, Any]:
    db.ensure_community_seeded()
    post = db.get_community_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/posts")
async def create_post(payload: PostCreate) -> dict[str, Any]:
    post = db.create_community_post(
        author_name=payload.author_name.strip(),
        body=payload.body.strip(),
    )

    try:
        send_community_notification(
            name=post["author_name"],
            message=post["body"],
        )
    except Exception:
        pass

    return {"ok": True, "post": post}


@router.post("/posts/{post_id}/replies")
async def create_reply(post_id: int, payload: ReplyCreate) -> dict[str, Any]:
    if not db.get_community_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found")

    try:
        reply = db.create_community_reply(
            post_id=post_id,
            author_name=payload.author_name.strip(),
            body=payload.body.strip(),
            parent_reply_id=payload.parent_reply_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"ok": True, "reply": reply}
