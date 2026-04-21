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

def get_config_path(filename: str):
    return os.path.join(os.path.dirname(__file__), "config", filename)

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
async def start_bot(background_tasks: BackgroundTasks):
    try:
        # Start supervisor or runAiBot
        cwd = os.path.dirname(__file__)
        subprocess.Popen(["python", "supervisor.py"], cwd=cwd)
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
