import os
import sys

# Ensure modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Override environment variables for testing OpenClaw
os.environ["AI_PROVIDER"] = "openclaw"
os.environ["USE_AI"] = "True"

from modules.ai.openclawConnections import ai_create_openai_client, ai_answer_question

def test_openclaw():
    print("====================================")
    print("Testing OpenClaw integration...")
    try:
        print("1. Initializing Client...")
        client = ai_create_openai_client()
        if client:
            print("[SUCCESS] Client initialized successfully!")
        else:
            print("[FAIL] Client returned None.")
            return

        print("\n2. Testing QA Generation...")
        question = "What are the key benefits of using open source AI models?"
        print(f"   Question: {question}")
        answer = ai_answer_question(client=client, question=question, stream=False)
        
        if answer:
            print(f"\n[SUCCESS] Answer received:\n{answer}")
        else:
            print("\n[FAIL] No answer generated.")

    except Exception as e:
        print(f"\n[ERROR] An exception occurred during testing: {e}")
        print("Note: If the error is a connection error, it means OpenClaw server might not be running or the URL in secrets is incorrect.")

if __name__ == "__main__":
    test_openclaw()
