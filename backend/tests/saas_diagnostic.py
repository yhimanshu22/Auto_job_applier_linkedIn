import os
import sys
import json
import tempfile

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_manager import db
from utils.encryption import decrypt_data
from services.storage import storage_service

def run_diagnostic():
    print("--- SaaS Cloud-Readiness Diagnostic ---")
    
    # 1. Check Encryption
    print("\n[1/3] Checking Database Encryption...")
    with db.get_session() as session:
        from models import Config
        api_key_row = session.get(Config, "llm_api_key")
        if api_key_row:
            if api_key_row.is_encrypted:
                raw_val = api_key_row.value
                decrypted = decrypt_data(raw_val)
                print(f"  [OK] SUCCESS: 'llm_api_key' is encrypted in DB.")
                print(f"  [INFO] Encrypted Preview: {raw_val[:20]}...")
            else:
                print("  [ERROR] FAIL: 'llm_api_key' found but is NOT encrypted.")
        else:
            print("  [WARN] WARNING: No 'llm_api_key' found in DB to test.")

    # 2. Check Session Management
    print("\n[2/3] Checking User Session Persistence...")
    test_cookies = {"li_at": "test_token_123"}
    db.set_user_session("diagnostic-user", test_cookies)
    retrieved = db.get_user_session("diagnostic-user")
    
    if retrieved == test_cookies:
        print("  [OK] SUCCESS: Encrypted sessions are working correctly.")
    else:
        print(f"  [ERROR] FAIL: Session mismatch. Expected {test_cookies}, got {retrieved}")

    # 3. Check Storage Abstraction
    print("\n[3/3] Checking Storage Abstraction...")
    test_content = b"PDF dummy content"
    test_filename = "diagnostic_resume.pdf"
    
    try:
        storage_path = storage_service.upload_file(test_content, test_filename, "diagnostic-user")
        db.upsert_resume_metadata("diagnostic-user", test_filename, storage_path)
        
        verified_content = storage_service.get_file_content(storage_path)
        if verified_content == test_content:
            print(f"  [OK] SUCCESS: Storage abstraction is working.")
            print(f"  [INFO] Storage Path: {storage_path}")
        else:
            print("  [ERROR] FAIL: Storage content mismatch.")
    except Exception as e:
        print(f"  [ERROR] FAIL: Storage error: {e}")

    print("\n--- Diagnostic Complete ---")

if __name__ == "__main__":
    run_diagnostic()
