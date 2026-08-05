import subprocess
from pathlib import Path

BLOCKED = ["rm -rf /", "sudo", "shutdown", "reboot", "mkfs", "dd if="]

def run_command(cmd: str, cwd: str = ".") -> dict:
    for blocked in BLOCKED:
        if blocked in cmd:
            return {"success": False, "output": f"Blocked command: {blocked}"}
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, cwd=cwd
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout + result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "Command timed out (30s limit)"}
    except Exception as e:
        return {"success": False, "output": str(e)}