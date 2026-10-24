import sys
import os
import io
import time
import socket
import threading
import subprocess
import webbrowser
import urllib.request

# Ensure sys.stdout and sys.stderr are valid objects in windowed/no-console mode
class SafeWriter:
    def write(self, s):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False

if sys.stdout is None:
    sys.stdout = SafeWriter()
elif not hasattr(sys.stdout, "isatty"):
    sys.stdout.isatty = lambda: False

if sys.stderr is None:
    sys.stderr = SafeWriter()
elif not hasattr(sys.stderr, "isatty"):
    sys.stderr.isatty = lambda: False

if sys.stdin is None:
    sys.stdin = io.StringIO()

if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def find_free_port(start_port=8000, max_port=8099):
    """Find the first available free port to avoid Errno 10048."""
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return 8000

def find_app_browser():
    """Look for Edge or Chrome executable for dedicated app-mode window."""
    candidate_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Edge\Application\msedge.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidate_paths:
        if p and os.path.exists(p):
            return p
    return None

def launch_desktop_window(url):
    """Launch dedicated frameless desktop window in app mode with isolated profile."""
    browser_exe = find_app_browser()
    if browser_exe:
        profile_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "fti_desktop_profile")
        try:
            os.makedirs(profile_dir, exist_ok=True)
        except Exception:
            pass

        cmd = [
            browser_exe,
            f"--app={url}",
            f"--user-data-dir={profile_dir}",
            "--window-size=1420,900",
            "--window-position=center",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions"
        ]
        try:
            proc = subprocess.Popen(cmd)
            return proc
        except Exception:
            pass

    # Fallback to standard browser
    try:
        webbrowser.open(url)
    except Exception:
        pass
    return None

def main():
    from logger_util import get_system_logger, PRIMARY_LOG_FILE
    logger = get_system_logger()

    port = find_free_port(start_port=8000, max_port=8099)
    url = f"http://127.0.0.1:{port}"

    from app import app, set_server_instance
    import uvicorn

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_config=None,
        access_log=False
    )
    server = uvicorn.Server(config)
    set_server_instance(server)

    # Start Uvicorn in background thread
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    # Wait for HTTP server to become responsive
    is_ready = False
    for _ in range(80):
        time.sleep(0.1)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/heartbeat", timeout=0.5) as r:
                if r.status == 200:
                    is_ready = True
                    break
        except Exception:
            continue

    if is_ready:
        logger.info("=================================================================", component="MAIN")
        logger.info(f"   FTI IT Asset Inventory Compare - MVP Desktop Running", component="MAIN")
        logger.info(f"   URL: {url}", component="MAIN")
        logger.info(f"   Log File: {PRIMARY_LOG_FILE}", component="MAIN")
        logger.info("=================================================================", component="MAIN")
    else:
        logger.error(f"Failed to start backend server on port {port}", component="MAIN")

    # Launch desktop window
    browser_proc = launch_desktop_window(url)

    # Monitor lifecycle (Clean shutdown on window close or exit button)
    try:
        while not server.should_exit:
            time.sleep(1)
            # If the dedicated browser window process exited (user clicked X)
            if browser_proc is not None and browser_proc.poll() is not None:
                time.sleep(2)
                if browser_proc.poll() is not None:
                    logger.info("Desktop application window closed. Shutting down server...", component="MAIN")
                    server.should_exit = True
                    break
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received. Exiting...", component="MAIN")
        server.should_exit = True

if __name__ == "__main__":
    main()
