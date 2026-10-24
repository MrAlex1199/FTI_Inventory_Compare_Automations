import sys
import os
import logging
import traceback
from datetime import datetime

# Configure UTF-8 for console output on Windows
if sys.platform == 'win32':
    try:
        if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Determine log file paths
LOG_FILENAME = "fti_debug.log"
CANDIDATE_LOG_DIRS = [
    os.getcwd(),
    os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)),
    "E:\\",
    os.environ.get("TEMP", "C:\\Temp")
]

log_filepaths = []
for d in CANDIDATE_LOG_DIRS:
    if d and os.path.exists(d):
        target = os.path.join(d, LOG_FILENAME)
        try:
            # Test write access
            with open(target, "a", encoding="utf-8") as f:
                f.write(f"\n--- FTI Asset Inventory Compare Log Session Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            log_filepaths.append(target)
            break
        except Exception:
            continue

PRIMARY_LOG_FILE = log_filepaths[0] if log_filepaths else os.path.join(os.environ.get("TEMP", "C:\\Temp"), LOG_FILENAME)

# Custom Multi-Handler Logger
class DualStreamLogger:
    """Streams log messages to both Console (stdout) and Log File."""
    def __init__(self, log_file):
        self.log_file = log_file

    def write(self, msg: str, level: str = "INFO", component: str = "SYSTEM"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [{level.upper():5}] [{component}] {msg}"
        
        # 1. Print to console
        try:
            print(formatted, flush=True)
        except Exception:
            try:
                print(formatted.encode("ascii", "replace").decode("ascii"), flush=True)
            except Exception:
                pass

        # 2. Append to log file
        try:
            with open(self.log_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(formatted + "\n")
        except Exception:
            pass

    def info(self, msg: str, component: str = "SYSTEM"):
        self.write(msg, "INFO", component)

    def warn(self, msg: str, component: str = "SYSTEM"):
        self.write(msg, "WARN", component)

    def error(self, msg: str, component: str = "SYSTEM", exc_info: bool = False):
        self.write(msg, "ERROR", component)
        if exc_info:
            tb = traceback.format_exc()
            self.write(tb, "ERROR", component)

    def debug(self, msg: str, component: str = "DEBUG"):
        self.write(msg, "DEBUG", component)

system_logger = DualStreamLogger(PRIMARY_LOG_FILE)

def get_system_logger():
    return system_logger

def log_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    system_logger.error(f"Unhandled Exception: {exc_value}", component="CRASH", exc_info=True)

sys.excepthook = log_unhandled_exception
