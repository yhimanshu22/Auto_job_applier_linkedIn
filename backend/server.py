from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os

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

# Global state to track the supervisor process
supervisor_process = None

@app.get("/api/config/{filename}")
async def read_config(filename: str):
    if filename not in ["personals.py", "search.py", "settings.py", "questions.py"]:
        raise HTTPException(status_code=400, detail="Invalid config file")
        
    path = get_config_path(filename)
    if not os.path.exists(path):
        return {"content": ""}
        
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@app.post("/api/config/{filename}")
async def write_config(filename: str, data: ConfigData):
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
        cwd = os.path.dirname(__file__)
        # On Windows, use subprocess.CREATE_NEW_CONSOLE to see the output if desired, 
        # or just run it in the background.
        supervisor_process = subprocess.Popen(
            ["python", "supervisor.py"], 
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
    if supervisor_process and supervisor_process.poll() is None:
        return {"status": "running"}
    return {"status": "stopped"}

@app.get("/api/bot/logs")
async def get_bot_logs():
    log_path = os.path.join(os.path.dirname(__file__), "logs", "supervisor.log")
    if not os.path.exists(log_path):
        return {"logs": "No logs found."}
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            # Return last 100 lines
            lines = f.readlines()
            return {"logs": "".join(lines[-100:])}
    except Exception as e:
        return {"logs": f"Error reading logs: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
