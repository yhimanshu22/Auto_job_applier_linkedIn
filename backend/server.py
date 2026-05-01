from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import sys
import uvicorn
import logging
from db_manager import db
import json

from routes.billing import router as billing_router

app = FastAPI(title="LinkedIn Bot API")

app.include_router(billing_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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
    "free": {
        "max_accounts": 0,
        "max_active_bots": 0,
        "monthly_applications": 0,
    },
    "starter": {
        "max_accounts": 1,
        "max_active_bots": 1,
        "monthly_applications": 100,
    },
    "pro": {
        "max_accounts": 3,
        "max_active_bots": 2,
        "monthly_applications": 500,
    },
    "agency": {
        "max_accounts": 10,
        "max_active_bots": 5,
        "monthly_applications": 3000,
    },
}

def assert_can_start_bot(user_id: str):
    subscription = db.get_user_subscription(user_id)

    if not subscription or subscription["status"] not in ["active", "trialing"]:
        raise HTTPException(
            status_code=402,
            detail="Active subscription required to start the bot",
        )

    plan = subscription.get("plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    # For now, we count configured accounts in .env as active bots
    # You would typically query DB to see how many bots are actually running
    active_accounts = []
    for key in os.environ:
        if key.startswith("LINKEDIN_USERNAME_") and key[18:]:
            active_accounts.append(key)
    
    active_bots = len(active_accounts) or 1 # Fallback to 1 if no suffix is used but default is set

    if active_bots > limits["max_active_bots"]:
        raise HTTPException(
            status_code=403,
            detail=f"Your {plan} plan allows only {limits['max_active_bots']} active bot(s). You have {active_bots} configured."
        )


@app.post("/api/bot/start")
async def start_bot(payload: dict = None):
    # Hardcoded local user for MVP
    user_id = payload.get("user_id", "local-user") if payload else "local-user"
    
    assert_can_start_bot(user_id)

    global supervisor_process
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
        
        supervisor_process = subprocess.Popen(
            cmd, 
            cwd=cwd,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
        current_run_id = db.start_bot_run("local-user")
        
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")
        
    try:
        content = await file.read()
        db.set_asset("default_resume", file.filename, content, "resumes")
        
        # Also update the default_resume_path in configs to point to a virtual path
        # Actually, we keep it as just "analyst.pdf" or whatever the filename is
        db.set_config("default_resume_path", file.filename, "questions")
        
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot/stop")
async def stop_bot():
    global supervisor_process
    if supervisor_process and supervisor_process.poll() is None:
        try:
            if os.name == 'nt':
                # Forcefully kill the process tree on Windows
                subprocess.run(["taskkill", "/F", "/PID", str(supervisor_process.pid), "/T"], capture_output=True)
            else:
                supervisor_process.terminate()
            
            supervisor_process = None
            
            if current_run_id:
                # Basic session count calculation logic could go here
                db.end_bot_run(current_run_id, 0)
                current_run_id = None
                
            return {"status": "stopped"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return {"status": "not_running"}

@app.get("/api/bot/status")
async def get_bot_status():
    global supervisor_process
    
    # Get limit from settings
    # Get limit from DB
    daily_apply_limit = db.get_config("daily_apply_limit", 50)
    
    # Get current count from CSV
    applied_count = 0
    file_name = db.get_config("file_name", "all excels/all_applied_applications_history.csv")
    if os.path.exists(file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                # Subtract 1 for header
                applied_count = max(0, len(f.readlines()) - 1)
        except:
            pass

    status = "stopped"
    if supervisor_process and supervisor_process.poll() is None:
        status = "running"
        
    return {
        "status": status,
        "applied_count": applied_count,
        "limit": daily_apply_limit
    }

@app.get("/api/bot/logs")
async def get_bot_logs():
    log_path = os.path.join(os.getcwd(), "logs", "supervisor.log")
    if not os.path.exists(log_path):
        return {"logs": "No logs available. Start the bot to see activity."}
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            # Return last 100 lines
            lines = f.readlines()
            return {"logs": "".join(lines[-100:])}
    except Exception as e:
        return {"logs": f"Error reading logs: {str(e)}"}

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
