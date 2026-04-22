from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import sys
import uvicorn

app = FastAPI(title="LinkedIn Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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

@app.get("/api/config/{filename}")
async def read_config(filename: str):
    # Support both "personals" and "personals.py"
    if not filename.endswith(".py"):
        filename += ".py"
        
    if filename not in ["personals.py", "search.py", "settings.py", "questions.py"]:
        raise HTTPException(status_code=400, detail="Invalid config file")
        
    path = get_config_path(filename)
    if not os.path.exists(path):
        return {"content": ""}
        
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@app.post("/api/config/{filename}")
async def write_config(filename: str, data: ConfigData):
    if not filename.endswith(".py"):
        filename += ".py"
        
    if filename not in ["personals.py", "search.py", "settings.py", "questions.py"]:
        raise HTTPException(status_code=400, detail="Invalid config file")
        
    path = get_config_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data.content)
    return {"status": "success"}

@app.post("/api/bot/start")
async def start_bot():
    global supervisor_process
    if supervisor_process and supervisor_process.poll() is None:
        return {"status": "already_running"}
        
    try:
        # Use sys.executable to spawn the current runner (Python or EXE)
        # This is critical for standalone EXE production environments
        cmd = [sys.executable, "--supervisor"]
        
        cwd = get_base_path()
        logging.info(f"Starting supervisor with {cmd} in {cwd}")
        
        supervisor_process = subprocess.Popen(
            cmd, 
            cwd=cwd,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        return {"status": "started"}
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
            return {"status": "stopped"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return {"status": "not_running"}

@app.get("/api/bot/status")
async def get_bot_status():
    global supervisor_process
    
    # Get limit from settings
    from config.settings import daily_apply_limit
    
    # Get current count from CSV
    applied_count = 0
    from config.settings import file_name
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
        uvicorn.run(app, host="0.0.0.0", port=8000)
