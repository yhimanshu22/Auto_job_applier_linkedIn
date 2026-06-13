"""
FastAPI entrypoint: middleware, router registration, and CLI modes (--bot / --supervisor / uvicorn).
"""

import os
import sys

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.secrets import load_all_secrets

load_all_secrets([
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "PAYU_MERCHANT_KEY",
    "PAYU_MERCHANT_SALT",
    "NEXTAUTH_SECRET",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "ENCRYPTION_KEY",
    "DATABASE_URL",
])

from routes.billing import router as billing_router
from routes.applications import router as applications_router
from routes.bot import router as bot_router
from routes.config_routes import router as config_router
from routes.health import router as health_router
from routes.linkedin_accounts import router as linkedin_accounts_router
from routes.linkedin_automation import router as linkedin_automation_router
from routes.uploads import router as uploads_router

from db_manager import db


@asynccontextmanager
async def _app_lifespan(app: FastAPI):
    import logging

    log = logging.getLogger(__name__)
    try:
        n = db.reconcile_stale_automation_tasks()
        if n:
            log.warning(
                "Reconciled %s automation task(s) stuck as running (no live process).",
                n,
            )
    except Exception:
        log.exception("Stale automation task reconcile failed")
    yield


app = FastAPI(title="LinkedIn Bot API", lifespan=_app_lifespan)

app.include_router(billing_router)
app.include_router(applications_router, prefix="/api/applications")
app.include_router(bot_router)
app.include_router(config_router)
app.include_router(health_router)
app.include_router(linkedin_accounts_router)
app.include_router(linkedin_automation_router)
app.include_router(uploads_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.56.1:3000",
        os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    if "--bot" in sys.argv:
        from runAiBot import main

        main()
    elif "--supervisor" in sys.argv:
        from supervisor import main

        main()
    else:
        uvicorn.run(app, host="127.0.0.1", port=8000)
