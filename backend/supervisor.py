import subprocess
import time
import sys
import os
import signal
import logging
from datetime import datetime
from dotenv import load_dotenv

from app_paths import get_logs_dir, get_runtime_writable_root

# Load environment variables
load_dotenv()


def _nt_background_creationflags():
    """Hide console windows for child processes on Windows (no CMD popup)."""
    if os.name != "nt":
        return 0
    # Python 3.7+ on Windows
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


# Configure logging (canonical app logs dir, not cwd-relative)
_LOG_DIR = get_logs_dir()
os.makedirs(_LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(_LOG_DIR, "supervisor.log")),
        logging.StreamHandler(sys.stdout)
    ]
)

class BotSupervisor:
    def __init__(self):
        self.bot_processes = {}  # Map bot_id -> subprocess.Popen
        self._bot_log_handles = {}  # Keep stdout log files open while children run
        self.accounts = self._get_accounts()
        self.is_running = True

    def _close_bot_stdio(self, bot_id):
        h = self._bot_log_handles.pop(bot_id, None)
        if h:
            try:
                h.close()
            except Exception:
                pass

    def _get_accounts(self):
        """Identifies all LinkedIn accounts from environment variables."""
        accounts = []
        # Support both the original format and the new multi-account format
        default_user = os.getenv("LINKEDIN_USERNAME")
        default_pass = os.getenv("LINKEDIN_PASSWORD")
        
        if default_user and default_pass:
            accounts.append({
                "id": "main",
                "username": default_user,
                "password": default_pass
            })

        # Look for LINKEDIN_USERNAME_N patterns
        for key, value in os.environ.items():
            if key.startswith("LINKEDIN_USERNAME_") and key[18:]:
                suffix = key[18:]
                password = os.getenv(f"LINKEDIN_PASSWORD_{suffix}")
                if password:
                    accounts.append({
                        "id": suffix,
                        "username": value,
                        "password": password
                    })
        
        logging.info(f"Identified {len(accounts)} accounts: {[a['id'] for a in accounts]}")
        return accounts

    def start_bot(self, account):
        """Starts the runAiBot.py process for a specific account."""
        bot_id = account["id"]
        try:
            logging.info(f"Preparing to start runAiBot.py for account {bot_id} ({account['username']})...")
            
            # Create a specific environment for this bot
            env = os.environ.copy()
            env["LINKEDIN_USERNAME"] = account["username"]
            env["LINKEDIN_PASSWORD"] = account["password"]
            env["BOT_ID"] = bot_id
            
            # When running as an EXE, sys.executable is the EXE itself.
            # We use the --bot flag to trigger the bot logic in server.py
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable, "--bot"]
            else:
                import server
                server_script = os.path.join(os.path.dirname(os.path.abspath(server.__file__)), "server.py")
                cmd = [sys.executable, server_script, "--bot"]

            logging.info(f"[Supervisor] Starting bot with command: {cmd}")

            safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in bot_id)
            self._close_bot_stdio(bot_id)
            bot_stdio_log = os.path.join(_LOG_DIR, f"bot-{safe_id}-stdout.log")
            log_f = open(bot_stdio_log, "a", encoding="utf-8", buffering=1)
            self._bot_log_handles[bot_id] = log_f

            self.bot_processes[bot_id] = subprocess.Popen(
                cmd,
                cwd=get_runtime_writable_root(),
                env=env,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                creationflags=_nt_background_creationflags(),
            )
            logging.info(f"Bot {bot_id} started (PID: {self.bot_processes[bot_id].pid})")
        except Exception as e:
            logging.error(f"Failed to start Bot {bot_id}: {e}")

    def stop_all(self):
        """Stops all managed processes."""
        self.is_running = False
        logging.info("Stopping all processes...")
        
        for bot_id, process in self.bot_processes.items():
            try:
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/PID", str(process.pid), "/T"], capture_output=True)
                else:
                    process.terminate()
                logging.info(f"Bot process {bot_id} stopped.")
            except Exception as e:
                logging.error(f"Error stopping bot {bot_id}: {e}")
            self._close_bot_stdio(bot_id)

    def run(self):
        """Main supervisor loop."""
        while self.is_running:
            for account in self.accounts:
                bot_id = account["id"]
                process = self.bot_processes.get(bot_id)
                
                if process is None or process.poll() is not None:
                    if process:
                        exit_code = process.poll()
                        # 0: Standard normal exit
                        # 3221225786 (0xC000013A): User closed console or Ctrl+C on Windows
                        if exit_code in [0, 3221225786, -1073741510]:
                            logging.info(f"Bot {bot_id} was terminated by user (code {exit_code}). Not restarting.")
                            # Remove from active processes so we don't keep checking it
                            del self.bot_processes[bot_id]
                            self._close_bot_stdio(bot_id)
                            # Remove from accounts so it doesn't get picked up again in next iteration
                            self.accounts = [a for a in self.accounts if a["id"] != bot_id]
                            continue
                        
                        logging.warning(f"Bot {bot_id} exited with code {exit_code}. Restarting in 30 seconds...")
                        time.sleep(30)
                    
                    self.start_bot(account)
                    
                    # Stagger startup to avoid Chrome initialization conflicts
                    if len(self.accounts) > 1:
                        logging.info("Waiting 15 seconds before checking next account for staggered startup...")
                        time.sleep(15)

            time.sleep(10)

def main():
    supervisor = BotSupervisor()

    def handle_exit(signum, frame):
        supervisor.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    logging.info("--- Supervisor Started ---")
    supervisor.run()

if __name__ == "__main__":
    main()
