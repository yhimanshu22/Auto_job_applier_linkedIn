import sys
import os
import importlib.util
import json

# Add current directory to path so we can import db_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_manager import db

def migrate_file(file_path, category):
    print(f"--- Migrating {file_path} (category: {category}) ---")
    
    # dynamic import
    spec = importlib.util.spec_from_file_location(category, file_path)
    module = importlib.util.module_from_spec(spec)
    
    # We need to handle potential imports inside the config files
    # personals.py is often imported by others
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"Warning: Could not fully execute {file_path}: {e}")
        # If it fails due to missing imports, we might need to add config dir to sys.path
        config_dir = os.path.dirname(file_path)
        if config_dir not in sys.path:
            sys.path.append(config_dir)
        spec.loader.exec_module(module)
    
    # Filter out built-in attributes and common modules/functions
    keys = [k for k in dir(module) if not k.startswith('__')]
    
    imported_names = ['os', 'json', 'sys', 're', 'pyautogui', 'datetime', 'time', 'randint', 'choice', 'shuffle', 'Select', 'By', 'EC', 'WebDriverWait', 'WebElement']
    
    for key in keys:
        value = getattr(module, key)
        # Check if it's a constant (not a module, function, or class)
        if not callable(value) and not isinstance(value, type(os)) and key not in imported_names:
            try:
                db.set_config(key, value, category)
                print(f"  [OK] {key}")
            except Exception as e:
                print(f"  [FAIL] {key}: {e}")

if __name__ == "__main__":
    # Correct base path for migration
    base_dir = os.getcwd()
    # Check if we are in backend dir already
    if os.path.exists("config") and not os.path.exists("backend/config"):
        base_dir = os.getcwd()
    elif os.path.exists("backend/config"):
        base_dir = os.path.join(os.getcwd(), "backend")
    else:
        print("Error: Could not find config directory.")
        sys.exit(1)

    config_dir = os.path.join(base_dir, "config")
    files = ["personals.py", "search.py", "settings.py", "questions.py", "secrets.py"]
    
    for f in files:
        path = os.path.join(config_dir, f)
        if os.path.exists(path):
            category = f.replace(".py", "")
            migrate_file(path, category)
        else:
            print(f"Skipping {f} (not found at {path})")

    print("\nMigration complete. Data stored in backend/data.db")
    db.close()
