from __future__ import annotations

import re
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from db_manager import db
from services.email import send_feedback_email

router = APIRouter(prefix="/api/community", tags=["community"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PostType = Literal["feedback", "question"]


def _validate_email(value: str) -> str:
    email = value.strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValueError("Invalid email address")
    return email


class PostCreate(BaseModel):
    author_name: str = Field(min_length=1, max_length=120)
    author_email: str = Field(min_length=3, max_length=254)
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=10, max_length=4000)
    post_type: PostType = "feedback"
    rating: int | None = Field(default=None, ge=1, le=5)

    @field_validator("author_email")
    @classmethod
    def validate_author_email(cls, value: str) -> str:
        return _validate_email(value)


class ReplyCreate(BaseModel):
    author_name: str = Field(min_length=1, max_length=120)
    author_email: str = Field(min_length=3, max_length=254)
    body: str = Field(min_length=2, max_length=2000)
    parent_reply_id: int | None = None

    @field_validator("author_email")
    @classmethod
    def validate_author_email(cls, value: str) -> str:
        return _validate_email(value)


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
        author_email=payload.author_email,
        title=payload.title.strip(),
        body=payload.body.strip(),
        post_type=payload.post_type,
        rating=payload.rating,
    )

    try:
        send_feedback_email(
            name=post["author_name"],
            email=post["author_email"],
            message=f"[{post['post_type']}] {post['title']}\n\n{post['body']}",
            rating=post.get("rating"),
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
            author_email=payload.author_email,
            body=payload.body.strip(),
            parent_reply_id=payload.parent_reply_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"ok": True, "reply": reply}
