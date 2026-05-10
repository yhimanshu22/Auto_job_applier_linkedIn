from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import subprocess
import os
import sys
import glob
from datetime import datetime, timezone
import uvicorn
import logging
from db_manager import db
import json
from utils.secrets import load_all_secrets

# Load critical secrets from GCP Secret Manager in production
load_all_secrets([
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "NEXTAUTH_SECRET",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "ENCRYPTION_KEY",
    "DATABASE_URL"
])

from routes.billing import router as billing_router
from routes.applications import router as applications_router
from services.storage import storage_service

app = FastAPI(title="LinkedIn Bot API")

app.include_router(billing_router)
app.include_router(applications_router, prefix="/api/applications")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.56.1:3000",
        os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip('/')
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "backend",
        "version": "1.1.0"
    }

@app.get("/api/version")
async def get_version():
    return {"version": "1.1.0"}

class ConfigData(BaseModel):
    content: str

def get_base_path():
    """Returns the base path for the application, handling both script and EXE modes."""
    if getattr(sys, 'frozen', False):
        # Running as EXE (PyInstaller)
        base_path = os.path.dirname(sys.executable)
        # In dev mode, if running from dist/, the config folder is one level up
        if os.path.basename(base_path) == "dist":
             return os.path.dirname(base_path)
        return base_path
    # Running as plain Python script
    return os.path.dirname(os.path.abspath(__file__))

def get_config_path(filename: str):
    return os.path.join(get_base_path(), "config", filename)

# Global state to track the supervisor process
supervisor_process = None
current_run_id = None
supervisor_log_handle = None


def _close_supervisor_log():
    global supervisor_log_handle
    if supervisor_log_handle:
        try:
            supervisor_log_handle.flush()
            supervisor_log_handle.close()
        except Exception:
            pass
        supervisor_log_handle = None


def _apply_dashboard_linkedin_credentials(env: dict) -> None:
    """
    Inject LinkedIn credentials from DB (dashboard) into env for the supervisor / bot:
    - Primary: username + password -> LINKEDIN_USERNAME, LINKEDIN_PASSWORD
    - Additional: linkedin_extra_accounts JSON -> LINKEDIN_USERNAME_1..N, LINKEDIN_PASSWORD_1..N
    """
    try:
        secrets_cfg = db.get_all_by_category("secrets")
    except Exception:
        logging.warning("Could not read secrets from DB for LinkedIn credentials.")
        return
    user = secrets_cfg.get("username")
    password = secrets_cfg.get("password")
    if user and str(user).strip():
        env["LINKEDIN_USERNAME"] = str(user).strip()
    if password is not None and str(password).strip() != "":
        env["LINKEDIN_PASSWORD"] = str(password)

    extras = secrets_cfg.get("linkedin_extra_accounts")
    if isinstance(extras, list):
        for i, acc in enumerate(extras, start=1):
            if not isinstance(acc, dict):
                continue
            u = (acc.get("username") or "").strip()
            p = acc.get("password")
            if not u or p is None or str(p).strip() == "":
                continue
            env[f"LINKEDIN_USERNAME_{i}"] = u
            env[f"LINKEDIN_PASSWORD_{i}"] = str(p)


def _preview_env_with_dashboard_credentials() -> dict:
    env = os.environ.copy()
    _apply_dashboard_linkedin_credentials(env)
    return env


def _count_linkedin_accounts(env: dict) -> int:
    """Match supervisor.BotSupervisor._get_accounts — count distinct runnable accounts."""
    n = 0
    du = env.get("LINKEDIN_USERNAME")
    dp = env.get("LINKEDIN_PASSWORD")
    if du and dp:
        n += 1
    for key, value in env.items():
        if key.startswith("LINKEDIN_USERNAME_") and key[18:] and value:
            suffix = key[18:]
            if env.get(f"LINKEDIN_PASSWORD_{suffix}"):
                n += 1
    return n


class LinkedInExtraRow(BaseModel):
    username: str = ""
    password: str = ""


class LinkedInAccountsSave(BaseModel):
    primary_username: str = ""
    primary_password: str = ""
    extras: list[LinkedInExtraRow] = Field(default_factory=list)


@app.get("/api/linkedin-accounts")
async def get_linkedin_accounts():
    """LinkedIn accounts stored for the bot (passwords not echoed)."""
    try:
        s = db.get_all_by_category("secrets")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    extras_raw = s.get("linkedin_extra_accounts")
    if not isinstance(extras_raw, list):
        extras_raw = []

    extras_out = []
    for row in extras_raw:
        if isinstance(row, dict) and row.get("username"):
            extras_out.append(
                {
                    "username": str(row.get("username", "")),
                    "password_set": bool(row.get("password")),
                }
            )

    return {
        "primary_username": (s.get("username") or ""),
        "primary_password_set": bool(s.get("password")),
        "extras": extras_out,
    }


@app.post("/api/linkedin-accounts")
async def save_linkedin_accounts(body: LinkedInAccountsSave):
    """Save primary + additional LinkedIn accounts (password optional = keep previous)."""
    try:
        existing = db.get_all_by_category("secrets")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    db.set_config("username", body.primary_username.strip(), "secrets")

    if body.primary_password.strip():
        db.set_config("password", body.primary_password, "secrets")

    old_extras = existing.get("linkedin_extra_accounts")
    if not isinstance(old_extras, list):
        old_extras = []

    old_by_username = {}
    for row in old_extras:
        if isinstance(row, dict) and row.get("username"):
            old_by_username[str(row["username"]).strip().lower()] = row

    merged: list[dict] = []
    for row in body.extras:
        u = row.username.strip()
        if not u:
            continue
        pw = row.password
        if not pw:
            prev = old_by_username.get(u.lower())
            if prev and prev.get("password"):
                pw = prev.get("password")
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Password required for LinkedIn account {u} (new account).",
                )
        merged.append({"username": u, "password": pw})

    db.set_config("linkedin_extra_accounts", merged, "secrets")
    return {"status": "saved", "account_count": _count_linkedin_accounts(_preview_env_with_dashboard_credentials())}


@app.get("/api/config/{category}")
async def read_config(category: str):
    # Support both "personals" and "personals.py"
    if category.endswith(".py"):
        category = category[:-3]
        
    if category not in ["personals", "search", "settings", "questions", "secrets"]:
        raise HTTPException(status_code=400, detail="Invalid config category")
        
    config_data = db.get_all_by_category(category)
    
    # Synthesize "pseudo-Python" content for the frontend editor to maintain compatibility
    # This keeps the current UI working while data is in DB
    content = f"################ {category.upper()} CONFIGURATION ################\n\n"
    for key, value in config_data.items():
        if isinstance(value, str):
            content += f'{key} = "{value}"\n'
        else:
            content += f'{key} = {value}\n'
            
    return {"content": content}

@app.post("/api/config/{category}")
async def write_config(category: str, data: ConfigData):
    if category.endswith(".py"):
        category = category[:-3]
        
    if category not in ["personals", "search", "settings", "questions", "secrets"]:
        raise HTTPException(status_code=400, detail="Invalid config category")
        
    # Parse the pseudo-Python back into keys/values
    # Note: This is an intermediate step until the UI is updated to use forms
    lines = data.content.split("\n")
    for line in lines:
        if "=" in line and not line.startswith("#"):
            try:
                parts = line.split("=", 1)
                key = parts[0].strip()
                value_str = parts[1].strip()
                
                # Basic parsing for strings, ints, bools, lists
                if (value_str.startswith('"') and value_str.endswith('"')) or (value_str.startswith("'") and value_str.endswith("'")):
                    value = value_str[1:-1]
                elif value_str.lower() == "true":
                    value = True
                elif value_str.lower() == "false":
                    value = False
                elif value_str.isdigit():
                    value = int(value_str)
                elif value_str.startswith("[") and value_str.endswith("]"):
                    # Use JSON parser for lists
                    try:
                        # Clean up python-style list for JSON parser if needed, 
                        # but simple lists like ["a", "b"] are valid JSON
                        value = json.loads(value_str.replace("'", '"'))
                    except:
                        value = value_str # Fallback to string
                else:
                    try:
                        value = float(value_str)
                    except:
                        value = value_str
                        
                db.set_config(key, value, category)
            except Exception as e:
                print(f"Error parsing line: {line} - {e}")
                
    return {"status": "success"}

PLAN_LIMITS = {
    "free_trial": {
        "max_accounts": 1,
        "max_active_bots": 1,
        "monthly_applications": 10,
        "trial_hours": 24,
        "ai_answers": False,
        "priority_support": False,
        "export_history": False,
    },
    "starter": {
        "max_accounts": 1,
        "max_active_bots": 1,
        "monthly_applications": 100,
        "ai_answers": False,
        "priority_support": False,
        "export_history": False,
    },
    "pro": {
        "max_accounts": 3,
        "max_active_bots": 2,
        "monthly_applications": 500,
        "ai_answers": True,
        "priority_support": True,
        "export_history": True,
    },
    "agency": {
        "max_accounts": 10,
        "max_active_bots": 5,
        "monthly_applications": 3000,
        "ai_answers": True,
        "priority_support": True,
        "export_history": True,
    },
}

def assert_can_start_bot(user_id: str):
    # Administrative Bypass for Project Admin
    if user_id in ["himu09854@gmail.com", "local-user"]:
        return

    subscription = db.get_user_subscription(user_id)

    if not subscription or subscription["status"] not in ["active", "trialing"]:
        raise HTTPException(
            status_code=402,
            detail="Active subscription or trial required to start the bot",
        )

    # Check for trial expiration
    if subscription["status"] == "trialing" and subscription.get("current_period_end"):
        is_expired = False
        try:
            # ISO format date string from DB
            expiry = datetime.fromisoformat(subscription["current_period_end"])
            if datetime.utcnow() > expiry:
                is_expired = True
        except Exception as e:
            print(f"Error checking trial expiry: {e}")
            
        if is_expired:
            # Mark as expired in DB
            db.upsert_subscription(user_id=user_id, status="expired")
            raise HTTPException(
                status_code=402,
                detail="Your 24-hour free trial has expired. Please upgrade to a paid plan to continue."
            )

    plan = subscription.get("plan", "free_trial")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free_trial"])
    
    # 1. Enforce Account Limits (same sources as supervisor: env + dashboard DB secrets)
    probe_env = _preview_env_with_dashboard_credentials()
    account_total = _count_linkedin_accounts(probe_env)

    if account_total > limits["max_accounts"]:
        raise HTTPException(
            status_code=403,
            detail=f"Your '{plan}' plan allows only {limits['max_accounts']} LinkedIn account(s). You have {account_total} configured."
        )

    if account_total == 0:
        raise HTTPException(
            status_code=400,
            detail="No LinkedIn accounts configured. Save credentials under Dashboard → secrets (LinkedIn) or set LINKEDIN_* in your environment.",
        )

    # 2. Enforce Monthly Application Limits
    applied_this_month = db.get_monthly_application_count(user_id)
    if applied_this_month >= limits["monthly_applications"]:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly application limit reached ({applied_this_month}/{limits['monthly_applications']}). Please upgrade your plan."
        )

    # 3. Enforce Active Bot Limits (configured accounts vs plan)
    if account_total > limits["max_active_bots"]:
        raise HTTPException(
            status_code=403,
            detail=f"Your '{plan}' plan allows only {limits['max_active_bots']} active bot(s). Please reduce your active accounts."
        )


@app.post("/api/bot/start")
async def start_bot(payload: dict = None):
    # Hardcoded local user for MVP
    user_id = payload.get("user_id", "local-user") if payload else "local-user"
    
    assert_can_start_bot(user_id)

    global supervisor_process, current_run_id, supervisor_log_handle
    if supervisor_process and supervisor_process.poll() is None:
        return {"status": "already_running"}
        
    try:
        # Use sys.executable to spawn the current runner (Python or EXE)
        # This is critical for standalone EXE production environments
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable, "--supervisor"]
        else:
            server_script = os.path.join(get_base_path(), "server.py")
            cmd = [sys.executable, server_script, "--supervisor"]
        
        cwd = get_base_path()
        logging.info(f"Starting supervisor with {cmd} in {cwd}")
        
        env = os.environ.copy()
        _apply_dashboard_linkedin_credentials(env)
        env["USER_ID"] = user_id

        # Capture supervisor stdout/stderr to logs/supervisor-console.log so the dashboard
        # (and Electron) can read them via /api/bot/logs. Avoid CREATE_NEW_CONSOLE so output
        # is not trapped in a separate window only.
        _close_supervisor_log()
        logs_dir = os.path.join(cwd, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        console_log = os.path.join(logs_dir, "supervisor-console.log")
        supervisor_log_handle = open(console_log, "a", encoding="utf-8", buffering=1)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        supervisor_log_handle.write(
            f"\n{'=' * 60}\n[{ts}] Supervisor session started (API / dashboard)\n{'=' * 60}\n"
        )
        supervisor_log_handle.flush()

        _sup_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        supervisor_process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=supervisor_log_handle,
            stderr=subprocess.STDOUT,
            creationflags=_sup_flags,
        )
        
        current_run_id = db.start_bot_run(user_id)
        
        return {"status": "started"}
    except Exception as e:
        _close_supervisor_log()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")
        
    # Hardcoded local user for MVP
    user_id = "local-user"
    
    try:
        content = await file.read()
        
        # 1. Upload to storage (Local or Cloud)
        storage_path = storage_service.upload_file(content, file.filename, user_id)
        
        # 2. Update metadata in DB
        db.upsert_resume_metadata(user_id, file.filename, storage_path, is_default=True)
        
        # 3. Maintain compatibility with old system for now
        db.set_config("default_resume_path", file.filename, "questions")
        
        return {"status": "success", "filename": file.filename, "storage_path": storage_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot/stop")
async def stop_bot():
    global supervisor_process, current_run_id
    try:
        if supervisor_process and supervisor_process.poll() is None:
            if os.name == 'nt':
                # Forcefully kill the process tree on Windows
                subprocess.run(["taskkill", "/F", "/PID", str(supervisor_process.pid), "/T"], capture_output=True)
            else:
                supervisor_process.terminate()
        
        # Always reset state even if process was already dead
        supervisor_process = None
        _close_supervisor_log()
        
        if current_run_id:
            db.end_bot_run(current_run_id, 0)
            current_run_id = None
            
        return {"status": "stopped"}
    except Exception as e:
        print(f"Error in stop_bot: {e}")
        # Even if killing fails, try to reset state
        supervisor_process = None
        current_run_id = None
        _close_supervisor_log()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bot/status")
async def get_bot_status(user_id: str = "local-user"):
    global supervisor_process
    
    # Get limits from plan
    subscription = db.get_user_subscription(user_id)
    plan = subscription.get("plan", "free_trial") if subscription else "free_trial"
    
    # Handle admin bypass for status display
    if user_id in ["himu09854@gmail.com", "local-user"]:
        plan = "agency"

    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free_trial"])
    
    # Get current count from DB
    stats = db.get_application_stats(user_id)
    applied_count = stats.get("applied", 0)

    status = "stopped"
    if supervisor_process and supervisor_process.poll() is None:
        status = "running"
        
    return {
        "status": status,
        "applied_count": applied_count,
        "limit": limits["monthly_applications"]
    }

@app.get("/api/bot/logs")
async def get_bot_logs(lines: int = 120):
    """Tail key bot log files under backend/logs (stable path via get_base_path).

    Returns legacy ``logs`` (concatenated text) plus structured ``infra`` and ``profiles``
    so the dashboard can show supervisor/gateway output separately from each LinkedIn worker (BOT_ID).
    """
    lines = max(20, min(int(lines), 500))
    log_dir = os.path.join(get_base_path(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    def tail_file(path: str) -> str:
        if not os.path.isfile(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                buf = f.readlines()
            return "".join(buf[-lines:])
        except Exception as ex:
            return f"(read error: {ex})"

    infra = []
    infra_text_parts = []
    for title, filename in (
        ("Supervisor console (stdout/stderr)", "supervisor-console.log"),
        ("Supervisor", "supervisor.log"),
        ("OpenClaw gateway", "openclaw.log"),
    ):
        path = os.path.join(log_dir, filename)
        chunk = tail_file(path).strip()
        if chunk:
            infra.append({"title": title, "filename": filename, "content": chunk})
            infra_text_parts.append(f"--- {title} ({filename}) ---\n{chunk}")

    profiles = []
    profile_text_parts = []
    for path in sorted(glob.glob(os.path.join(log_dir, "bot-*.txt"))):
        basename = os.path.basename(path)
        inner = basename[len("bot-") : -len(".txt")]
        chunk = tail_file(path).strip()
        profiles.append({"id": inner, "filename": basename, "content": chunk})
        if chunk:
            profile_text_parts.append(f"--- Bot profile {inner} ({basename}) ---\n{chunk}")

    legacy_parts = infra_text_parts + profile_text_parts
    if not legacy_parts:
        msg = (
            "No log files yet. Start the bot from the dashboard to capture supervisor output "
            f"under {log_dir}/."
        )
        return {"logs": msg, "infra": [], "profiles": []}

    return {
        "logs": "\n".join(legacy_parts),
        "infra": infra,
        "profiles": profiles,
    }

@app.get("/api/bot/runs")
async def get_bot_runs(limit: int = 10):
    runs = db.get_recent_bot_runs(limit)
    return {"runs": runs}

if __name__ == "__main__":
    import logging
    # Set up basic logging for when running via spawned process
    logging.basicConfig(level=logging.INFO)
    
    # Path/Mode logic
    if "--bot" in sys.argv:
        from runAiBot import main
        main()
    elif "--supervisor" in sys.argv:
        from supervisor import main
        main()
    else:
        # Standard server startup
        uvicorn.run(app, host="127.0.0.1", port=8000)
