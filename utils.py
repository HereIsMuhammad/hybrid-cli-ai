import os
import subprocess
import platform
from datetime import datetime
from pathlib import Path

# Path to history file in the user's home directory
HISTORY_FILE = Path.home() / ".cliai_history.txt"


def get_os_info() -> str:
    """
    Detects the current operating system and shell environment.
    Returns a SHORT tag (not a long sentence) so even small local
    models can follow it reliably in the system prompt.
    Possible values: 'gitbash', 'powershell', 'cmd', 'macos', 'linux'
    """
    os_name = platform.system()

    if os_name == "Windows":
        # Git Bash / MSYS2 / Cygwin set MSYSTEM or similar env vars
        if os.environ.get("MSYSTEM"):
            return "gitbash"
        if os.environ.get("PSModulePath"):
            return "powershell"
        return "cmd"

    elif os_name == "Darwin":
        return "macos"

    else:
        return "linux"


def execute_command(cmd: str):
    """Executes the shell command directly in the terminal."""
    try:
        # check=False handles commands that return non-zero on "no match" etc.
        result = subprocess.run(cmd, shell=True, check=False)
        if result.returncode != 0:
            print(f"\n[Note]: Process exited with code {result.returncode} "
                  f"(no matches found, or command may need elevated rights).")
    except Exception as e:
        print(f"\n[Error executing command]: {e}")


def save_to_history(prompt: str, command: str):
    """Logs the query, timestamp, and generated command to a local file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] PROMPT: {prompt} | CMD: {command}\n"

    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


def get_history(limit: int = 10) -> list:
    """Reads the last N commands from the history file."""
    if not HISTORY_FILE.exists():
        return []

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return lines[-limit:]


def clear_history():
    """Clears the history file content."""
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()