import subprocess
import time
import sys
import os
import signal
import logging
from datetime import datetime

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/supervisor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

class BotSupervisor:
    def __init__(self):
        self.bot_process = None
        self.openclaw_process = None
        self.is_running = True

    def start_openclaw(self):
        """Starts the OpenClaw gateway."""
        try:
            logging.info("Starting OpenClaw gateway...")
            # Redirect OpenClaw output to a log file for debugging
            log_file = open("logs/openclaw.log", "a")
            self.openclaw_process = subprocess.Popen(
                ["openclaw", "gateway", "--allow-unconfigured", "--port", "3000"],
                stdout=log_file,
                stderr=log_file,
                shell=True
            )
            logging.info(f"OpenClaw started (PID: {self.openclaw_process.pid})")
        except Exception as e:
            logging.error(f"Failed to start OpenClaw: {e}")

    def start_bot(self):
        """Starts the runAiBot.py process."""
        try:
            logging.info("Starting runAiBot.py...")
            self.bot_process = subprocess.Popen(
                [sys.executable, "runAiBot.py"],
                cwd=os.getcwd(),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            logging.info(f"Bot started (PID: {self.bot_process.pid})")
        except Exception as e:
            logging.error(f"Failed to start Bot: {e}")

    def stop_all(self):
        """Stops all managed processes."""
        self.is_running = False
        logging.info("Stopping all processes...")
        
        if self.bot_process:
            try:
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/PID", str(self.bot_process.pid), "/T"], capture_output=True)
                else:
                    self.bot_process.terminate()
                logging.info("Bot process stopped.")
            except Exception as e:
                logging.error(f"Error stopping bot: {e}")

        if self.openclaw_process:
            try:
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/PID", str(self.openclaw_process.pid), "/T"], capture_output=True)
                else:
                    self.openclaw_process.terminate()
                logging.info("OpenClaw process stopped.")
            except Exception as e:
                logging.error(f"Error stopping OpenClaw: {e}")

    def run(self):
        """Main supervisor loop."""
        self.start_openclaw()
        
        while self.is_running:
            if self.bot_process is None or self.bot_process.poll() is not None:
                if self.bot_process:
                    exit_code = self.bot_process.poll()
                    logging.warning(f"Bot process exited with code {exit_code}. Restarting in 30 seconds...")
                    time.sleep(30)
                
                self.start_bot()
            
            # Check OpenClaw (optional, usually quite stable)
            if self.openclaw_process and self.openclaw_process.poll() is not None:
                logging.warning("OpenClaw gateway crashed. Restarting...")
                self.start_openclaw()

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
