import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db_manager import db

router = APIRouter(prefix="/api", tags=["config"])


class ConfigData(BaseModel):
    content: str


@router.get("/config/{category}")
async def read_config(category: str):
    if category.endswith(".py"):
        category = category[:-3]

    if category not in ["personals", "search", "settings", "questions", "secrets"]:
        raise HTTPException(status_code=400, detail="Invalid config category")

    config_data = db.get_all_by_category(category)

    content = f"################ {category.upper()} CONFIGURATION ################\n\n"
    for key, value in config_data.items():
        if isinstance(value, str):
            content += f'{key} = "{value}"\n'
        else:
            content += f"{key} = {value}\n"

    return {"content": content}


@router.post("/config/{category}")
async def write_config(category: str, data: ConfigData):
    if category.endswith(".py"):
        category = category[:-3]

    if category not in ["personals", "search", "settings", "questions", "secrets"]:
        raise HTTPException(status_code=400, detail="Invalid config category")

    lines = data.content.split("\n")
    for line in lines:
        if "=" in line and not line.startswith("#"):
            try:
                parts = line.split("=", 1)
                key = parts[0].strip()
                value_str = parts[1].strip()

                if (value_str.startswith('"') and value_str.endswith('"')) or (
                    value_str.startswith("'") and value_str.endswith("'")
                ):
                    value = value_str[1:-1]
                elif value_str.lower() == "true":
                    value = True
                elif value_str.lower() == "false":
                    value = False
                elif value_str.isdigit():
                    value = int(value_str)
                elif value_str.startswith("[") and value_str.endswith("]"):
                    try:
                        value = json.loads(value_str.replace("'", '"'))
                    except Exception:
                        value = value_str
                else:
                    try:
                        value = float(value_str)
                    except Exception:
                        value = value_str

                db.set_config(key, value, category)
            except Exception as e:
                print(f"Error parsing line: {line} - {e}")

    return {"status": "success"}
