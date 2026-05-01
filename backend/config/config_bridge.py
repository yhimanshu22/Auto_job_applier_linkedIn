import sys
import os

# Ensure we can import db_manager from parent dir if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_manager import db

def load_config_to_module(module_name):
    # Default values to prevent crashes if DB keys are missing
    config_dict = {
        "file_name": "all excels/all_applied_applications_history.csv",
        "failed_file_name": "all excels/all_failed_applications_history.csv",
        "logs_folder_path": "logs/",
        "daily_apply_limit": 50,
        "run_in_background": False,
        "use_AI": True
    }
    
    categories = ["personals", "search", "settings", "questions", "secrets"]
    for cat in categories:
        config_dict.update(db.get_all_by_category(cat))
        
    if os.getenv("LINKEDIN_USERNAME"):
        config_dict["username"] = os.getenv("LINKEDIN_USERNAME")
    if os.getenv("LINKEDIN_PASSWORD"):
        config_dict["password"] = os.getenv("LINKEDIN_PASSWORD")
    
    current_module = sys.modules[module_name]
    for k, v in config_dict.items():
        setattr(current_module, k, v)
    return config_dict

# Initial load into this module so it can be imported with *
config_data = {
    "file_name": "all excels/all_applied_applications_history.csv",
    "failed_file_name": "all excels/all_failed_applications_history.csv",
    "logs_folder_path": "logs/",
    "daily_apply_limit": 50,
    "run_in_background": False,
    "use_AI": True
}
categories = ["personals", "search", "settings", "questions", "secrets"]
for cat in categories:
    config_data.update(db.get_all_by_category(cat))

if os.getenv("LINKEDIN_USERNAME"):
    config_data["username"] = os.getenv("LINKEDIN_USERNAME")
if os.getenv("LINKEDIN_PASSWORD"):
    config_data["password"] = os.getenv("LINKEDIN_PASSWORD")

# Export all keys to this module
for k, v in config_data.items():
    setattr(sys.modules[__name__], k, v)
