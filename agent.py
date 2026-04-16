"""
╔══════════════════════════════════════════════╗
║       J.A.R.V.I.S  DESKTOP  AGENT           ║
║    Run this on your MacBook to give Jarvis   ║
║    access to files, apps, and system info.   ║
╚══════════════════════════════════════════════╝

Usage:
    python agent.py                          (connects to localhost:8000)
    python agent.py wss://your-server.com    (connects to cloud server)
"""

import asyncio
import json
import os
import sys
import subprocess
import platform
import psutil
import websockets

# ── Config ──
AGENT_TOKEN = "jarvis-secret-2026"
DEFAULT_SERVER = "ws://localhost:8000"

# Safety: max file size to read (500KB)
MAX_FILE_SIZE = 500_000

# Blocked paths (never read these)
BLOCKED_PATTERNS = [
    ".ssh", ".env", "credentials", "secrets", "password",
    ".aws", ".gcloud", "keychain", "token",
]


def is_safe_path(path: str) -> bool:
    """Check if a file path is safe to read."""
    lower = path.lower()
    return not any(blocked in lower for blocked in BLOCKED_PATTERNS)


def handle_command(data: dict) -> dict:
    """Execute a command and return the result."""
    request_id = data.get("id", "")
    cmd_type = data.get("type", "")

    try:
        if cmd_type == "read_file":
            return read_file(request_id, data["path"])

        elif cmd_type == "list_files":
            return list_files(request_id, data.get("path", "~"))

        elif cmd_type == "open_app":
            return open_app(request_id, data["app"])

        elif cmd_type == "system_info":
            return get_system_info(request_id)

        else:
            return {"id": request_id, "status": "error", "error": f"Unknown command: {cmd_type}"}

    except Exception as e:
        return {"id": request_id, "status": "error", "error": str(e)}


def read_file(request_id: str, path: str) -> dict:
    """Read a file and return its contents."""
    path = os.path.expanduser(path)

    if not is_safe_path(path):
        return {"id": request_id, "status": "error", "error": "Access denied: sensitive file"}

    if not os.path.exists(path):
        return {"id": request_id, "status": "error", "error": f"File not found: {path}"}

    if os.path.getsize(path) > MAX_FILE_SIZE:
        return {"id": request_id, "status": "error", "error": "File too large (max 500KB)"}

    with open(path, "r", errors="replace") as f:
        content = f.read()

    return {
        "id": request_id,
        "status": "ok",
        "type": "file_content",
        "path": path,
        "content": content,
        "size": len(content),
    }


def list_files(request_id: str, path: str) -> dict:
    """List files in a directory."""
    path = os.path.expanduser(path)

    if not os.path.isdir(path):
        return {"id": request_id, "status": "error", "error": f"Not a directory: {path}"}

    entries = []
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        entry = {"name": name, "is_dir": os.path.isdir(full)}
        if not entry["is_dir"]:
            try:
                entry["size"] = os.path.getsize(full)
            except OSError:
                entry["size"] = 0
        entries.append(entry)

    return {
        "id": request_id,
        "status": "ok",
        "type": "file_list",
        "path": path,
        "entries": entries[:100],  # Max 100 entries
        "total": len(entries),
    }


def open_app(request_id: str, app_name: str) -> dict:
    """Open an application on macOS."""
    system = platform.system()
    if system == "Darwin":
        subprocess.Popen(["open", "-a", app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif system == "Windows":
        subprocess.Popen(["start", app_name], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen([app_name.lower()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return {"id": request_id, "status": "ok", "message": f"Opened {app_name}"}


def get_system_info(request_id: str) -> dict:
    """Get system information."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    battery = psutil.sensors_battery()

    info = {
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_total_gb": round(mem.total / (1024**3), 1),
        "disk_percent": disk.percent,
        "disk_total_gb": round(disk.total / (1024**3), 1),
        "platform": platform.platform(),
        "hostname": platform.node(),
    }

    if battery:
        info["battery_percent"] = battery.percent
        info["battery_plugged"] = battery.power_plugged

    return {"id": request_id, "status": "ok", "type": "system_info", "info": info}


async def main(server_url: str):
    """Connect to Jarvis server and handle commands."""
    ws_url = f"{server_url}/ws/agent?token={AGENT_TOKEN}"

    print("╔══════════════════════════════════════════════╗")
    print("║       J.A.R.V.I.S  DESKTOP  AGENT           ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"\n  Connecting to: {server_url}")

    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                print("  ✓ Connected to Jarvis server!")
                print("  MacBook is now accessible. Waiting for commands...\n")

                async for message in ws:
                    data = json.loads(message)
                    print(f"  → Command: {data.get('type', '?')}")

                    result = handle_command(data)
                    await ws.send(json.dumps(result))

                    status = result.get("status", "?")
                    print(f"  ← Result: {status}")

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            print(f"  ✗ Connection lost: {e}")
            print("  Reconnecting in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    server = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SERVER
    # Normalize URL
    if server.startswith("http://"):
        server = "ws://" + server[7:]
    elif server.startswith("https://"):
        server = "wss://" + server[8:]
    elif not server.startswith("ws"):
        server = "ws://" + server

    asyncio.run(main(server))
