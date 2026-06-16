from __future__ import annotations

from typing import Any

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from db_manager import db
from services.email import send_feedback_email

router = APIRouter(prefix="/api", tags=["feedback"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class FeedbackCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    message: str = Field(min_length=10, max_length=2000)
    rating: int | None = Field(default=None, ge=1, le=5)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not _EMAIL_RE.match(email):
            raise ValueError("Invalid email address")
        return email


@router.post("/feedback")
async def submit_feedback(payload: FeedbackCreate) -> dict[str, Any]:
    record = db.create_feedback(
        name=payload.name.strip(),
        email=str(payload.email).strip().lower(),
        message=payload.message.strip(),
        rating=payload.rating,
    )

    email_sent = False
    try:
        email_sent = send_feedback_email(
            name=record["name"],
            email=record["email"],
            message=record["message"],
            rating=record.get("rating"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Feedback saved but email could not be sent. Please try again later.",
        ) from exc

    return {
        "ok": True,
        "id": record["id"],
        "email_sent": email_sent,
    }
