from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db_manager import db
from services.email import send_feedback_email

router = APIRouter(prefix="/api/community", tags=["community"])


class PostCreate(BaseModel):
    author_name: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=10, max_length=4000)


class ReplyCreate(BaseModel):
    author_name: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=2, max_length=2000)
    parent_reply_id: int | None = None


def _title_from_body(body: str) -> str:
    line = body.strip().splitlines()[0].strip()
    if len(line) <= 200:
        return line
    return f"{line[:197]}..."


_ANON_EMAIL = "community-anonymous@linkdapply.local"


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
    body = payload.body.strip()
    post = db.create_community_post(
        author_name=payload.author_name.strip(),
        author_email=_ANON_EMAIL,
        title=_title_from_body(body),
        body=body,
        post_type="feedback",
        rating=None,
    )

    try:
        send_feedback_email(
            name=post["author_name"],
            email=_ANON_EMAIL,
            message=post["body"],
            rating=None,
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
            author_email=_ANON_EMAIL,
            body=payload.body.strip(),
            parent_reply_id=payload.parent_reply_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"ok": True, "reply": reply}
