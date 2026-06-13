"""
FastAPI entrypoint: middleware, router registration, and CLI modes (--bot / --supervisor / uvicorn).
"""

import os
import sys

from dotenv import load_dotenv

# Load backend/.env first, then optional user-data override (desktop sidecar).
load_dotenv()
_user_data = os.getenv("LINKDAPPLY_USER_DATA", "").strip()
if _user_data:
    load_dotenv(os.path.join(_user_data, ".env"), override=True)

# Bot subprocesses and early imports need env-backed secrets before DB is read.

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
    "LINKDAPPLY_INTERNAL_KEY",
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
from services.bot_supervisor import stop_supervisor
from utils.debug_logs import configure_api_logging

configure_api_logging()


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
    if stop_supervisor(reason="backend_shutdown"):
        log.info("Stopped job-applier supervisor on backend shutdown")
        try:
            from services import supervisor_state as sv

            if sv.current_run_id:
                db.end_bot_run(sv.current_run_id, 0)
                sv.current_run_id = None
        except Exception:
            log.exception("Failed to finalize bot run on shutdown")


app = FastAPI(title="LinkedIn Bot API", lifespan=_app_lifespan)

app.include_router(billing_router)
app.include_router(applications_router, prefix="/api/applications")
app.include_router(bot_router)
app.include_router(config_router)
app.include_router(health_router)
app.include_router(linkedin_accounts_router)
app.include_router(linkedin_automation_router)
app.include_router(uploads_router)

def _cors_origins() -> list[str]:
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.56.1:3000",
        os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/"),
    ]
    extra = os.getenv("EXTRA_CORS_ORIGINS", "").strip()
    if extra:
        origins.extend(o.strip().rstrip("/") for o in extra.split(",") if o.strip())
    # De-dupe while preserving order.
    seen: set[str] = set()
    unique: list[str] = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique.append(origin)
    return unique


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
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
        host = os.getenv("LINKDAPPLY_API_HOST", "127.0.0.1")
        port = int(os.getenv("LINKDAPPLY_API_PORT", "8000"))
        uvicorn.run(app, host=host, port=port)
