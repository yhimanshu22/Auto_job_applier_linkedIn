import subprocess
import time
import sys
import os
import signal

from app_paths import get_runtime_writable_root, load_env_files, subprocess_env
from utils.debug_logs import (
    SUPERVISOR_LOG,
    append_session_marker,
    bot_console_path,
    configure_file_logger,
)

# Load environment variables (backend/.env, not cwd-relative)
load_env_files()


def _nt_background_creationflags():
    """Hide console windows for child processes on Windows (no CMD popup)."""
    if os.name != "nt":
        return 0
    # Python 3.7+ on Windows
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


# Configure logging (canonical app logs dir, not cwd-relative)
logger = configure_file_logger("linkdapply.supervisor", SUPERVISOR_LOG)

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
        seen_usernames: set[str] = set()

        def _add(account_id: str, username: str, password: str) -> None:
            key = username.strip().lower()
            if not key or key in seen_usernames:
                return
            seen_usernames.add(key)
            accounts.append({
                "id": account_id,
                "username": username.strip(),
                "password": password,
            })

        default_user = os.getenv("LINKEDIN_USERNAME")
        default_pass = os.getenv("LINKEDIN_PASSWORD")

        if default_user and default_pass:
            _add("main", default_user, default_pass)

        indexed: list[tuple[str, str, str]] = []
        for key, value in os.environ.items():
            if key.startswith("LINKEDIN_USERNAME_") and key[18:]:
                suffix = key[18:]
                password = os.getenv(f"LINKEDIN_PASSWORD_{suffix}")
                if password and value:
                    indexed.append((suffix, value, password))

        def _suffix_sort(item: tuple[str, str, str]) -> tuple[int, object]:
            s = item[0]
            try:
                return (0, int(s))
            except ValueError:
                return (1, s)

        indexed.sort(key=_suffix_sort)
        for suffix, username, password in indexed:
            _add(suffix, username, password)

        logger.info(f"Identified {len(accounts)} accounts: {[a['id'] for a in accounts]}")
        return accounts

    def start_bot(self, account):
        """Starts the runAiBot.py process for a specific account."""
        bot_id = account["id"]
        try:
            logger.info(f"Preparing to start runAiBot.py for account {bot_id} ({account['username']})...")
            
            # Create a specific environment for this bot
            env = subprocess_env()
            env["LINKEDIN_USERNAME"] = account["username"]
            env["LINKEDIN_PASSWORD"] = account["password"]
            env["BOT_ID"] = bot_id
            if os.getenv("USER_ID"):
                env["USER_ID"] = os.getenv("USER_ID")
            
            # When running as an EXE, sys.executable is the EXE itself.
            # We use the --bot flag to trigger the bot logic in server.py
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable, "--bot"]
            else:
                import server
                server_script = os.path.join(os.path.dirname(os.path.abspath(server.__file__)), "server.py")
                cmd = [sys.executable, server_script, "--bot"]

            logger.info(f"[Supervisor] Starting bot with command: {cmd}")

            self._close_bot_stdio(bot_id)
            bot_stdio_log = bot_console_path(bot_id)
            append_session_marker(
                bot_stdio_log, f"Bot worker started (account={bot_id})"
            )
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
            logger.info(f"Bot {bot_id} started (PID: {self.bot_processes[bot_id].pid})")
        except Exception as e:
            logger.error(f"Failed to start Bot {bot_id}: {e}")

    def stop_all(self):
        """Stops all managed processes."""
        self.is_running = False
        logger.info("Stopping all processes...")
        
        for bot_id, process in self.bot_processes.items():
            try:
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/PID", str(process.pid), "/T"], capture_output=True)
                else:
                    process.terminate()
                logger.info(f"Bot process {bot_id} stopped.")
            except Exception as e:
                logger.error(f"Error stopping bot {bot_id}: {e}")
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
                        logger.info(
                            f"Bot {bot_id} exited (code {exit_code}). Not restarting."
                        )
                        del self.bot_processes[bot_id]
                        self._close_bot_stdio(bot_id)
                        self.accounts = [
                            a for a in self.accounts if a["id"] != bot_id
                        ]
                        continue

                    self.start_bot(account)
                    
                    # Stagger startup to avoid Chrome initialization conflicts
                    if len(self.accounts) > 1:
                        logger.info("Waiting 15 seconds before checking next account for staggered startup...")
                        time.sleep(15)

            if not self.accounts:
                logger.info("All bot workers have exited. Supervisor stopping.")
                break

            time.sleep(10)

def main():
    supervisor = BotSupervisor()

    def handle_exit(signum, frame):
        supervisor.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    logger.info("--- Supervisor Started ---")
    supervisor.run()

if __name__ == "__main__":
    main()
