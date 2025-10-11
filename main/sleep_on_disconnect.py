"""
Sleep-on-Disconnect
Minimal monitor that turns OFF the screen when your chosen Bluetooth device disconnects
or goes out of range. Quiet by default: no fancy UI, just the essential behavior.

How it works (Windows only):
- Detects currently connected Bluetooth devices via PowerShell (Get-PnpDevice)
- Auto-selects the first connected audio/device; if multiple, prompts once
- Monitors connection every 2.5s
- If disconnected for ~5s (2 consecutive checks), turns OFF the display using Win32 API

Notes:
- Moving the mouse or pressing a key will wake the screen.
- No auto-wake logic is needed; this tool only turns the screen off on disconnect.
"""

import json
import subprocess
import sys
import time
import ctypes
import os
from typing import Optional, List, Dict


CHECK_INTERVAL_SEC = 2.5
DISCONNECT_GRACE_CHECKS = 2  # require N consecutive misses (~5s) before sleeping display
FULL_SYSTEM_SLEEP = False     # set True to sleep the PC instead of just turning off display

# Persistent config to pin your preferred device
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CONFIG_PATH = os.path.join(ROOT_DIR, "sleep_config.json")


def load_config() -> Optional[Dict[str, str]]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and data.get("instance_id"):
                return {"name": data.get("name", "Bluetooth Device"), "instance_id": data["instance_id"]}
    except FileNotFoundError:
        return None
    except Exception:
        return None
    return None


def save_config(device: Dict[str, str]) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"name": device.get("name", "Bluetooth Device"), "instance_id": device["instance_id"]}, f)
    except Exception:
        pass


def _run_powershell(ps_script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def list_connected_bt_devices() -> List[Dict[str, str]]:
    """Return a list of currently connected Bluetooth devices with FriendlyName and InstanceId."""
    ps = (
        "Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq 'OK'} "
        "| Select-Object -Property FriendlyName, InstanceId | ConvertTo-Json -Compress"
    )
    cp = _run_powershell(ps)
    if cp.returncode != 0 or not cp.stdout.strip():
        return []
    try:
        data = json.loads(cp.stdout)
        if isinstance(data, dict):
            data = [data]
        # Normalize keys and remove empty names
        devices = []
        for d in data:
            name = (d.get("FriendlyName") or "").strip()
            iid = (d.get("InstanceId") or "").strip()
            if iid:
                devices.append({"name": name or "Bluetooth Device", "instance_id": iid})
        return devices
    except json.JSONDecodeError:
        return []


def is_device_connected(instance_id: str) -> bool:
    """Check if a device instance is currently Status OK in Windows."""
    # Quote the instance id for PowerShell
    ps = (
        f"$d = Get-PnpDevice -InstanceId \"{instance_id.replace('`', '``').replace('"', '`"')}\"; "
        "$d | Select-Object -ExpandProperty Status"
    )
    cp = _run_powershell(ps)
    if cp.returncode != 0:
        return False
    status = cp.stdout.strip()
    return status.upper() == "OK"


def turn_off_display():
    """Turn OFF monitor using Win32 SendMessage (no external tools)."""
    HWND_BROADCAST = 0xFFFF
    WM_SYSCOMMAND = 0x0112
    SC_MONITORPOWER = 0xF170
    # 2 = turn off, 1 = low power, -1 = on (ignored)
    try:
        ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2)
    except Exception:
        # Fallback: lock workstation if turning off display fails
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"]).returncode


def sleep_system():
    """Put system to sleep using powercfg (requires permissions)."""
    # On some systems, this may hibernate depending on power settings.
    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"]).returncode


def choose_device_interactive(devices: List[Dict[str, str]]) -> Dict[str, str]:
    """Deprecated: kept for reference. We now auto-select to avoid prompts."""
    # Auto-select the first device for non-interactive mode
    return devices[0]


def pick_device(override_instance_id: Optional[str] = None) -> Optional[Dict[str, str]]:
    # 1) If override provided, use that (and save)
    if override_instance_id:
        device = {"name": "Pinned Bluetooth Device", "instance_id": override_instance_id}
        save_config(device)
        return device

    # 2) Load pinned device from config if available
    cfg = load_config()
    if cfg and cfg.get("instance_id"):
        return cfg

    # 3) Otherwise, detect current connected devices and pin best match
    devices = list_connected_bt_devices()
    if not devices:
        return None
    preferred = [
        d for d in devices if any(k in d["name"].lower() for k in ("audio", "head", "ear", "buds", "speaker"))
    ]
    selected = preferred[0] if preferred else devices[0]
    save_config(selected)
    return selected


def main():
    # Simple CLI flags for testing
    max_checks = None  # type: Optional[int]
    no_sleep = False
    args = sys.argv[1:]
    if "--once" in args:
        max_checks = 1
    if "--no-sleep" in args:
        no_sleep = True
    if "--max-checks" in args:
        try:
            i = args.index("--max-checks")
            max_checks = int(args[i + 1])
        except Exception:
            pass
    override_id = None
    if "--device-id" in args:
        try:
            j = args.index("--device-id")
            override_id = args[j + 1]
        except Exception:
            override_id = None
    device = pick_device(override_instance_id=override_id)
    if not device:
        print("No connected Bluetooth device found. Connect your device and run again.")
        sys.exit(1)

    name = device["name"]
    iid = device["instance_id"]
    print(f"Monitoring: {name}")
    print("Disconnect => display off" + (" (full sleep)" if FULL_SYSTEM_SLEEP else ""))

    consecutive_misses = 0
    has_slept = False

    try:
        checks_done = 0
        while True:
            connected = is_device_connected(iid)
            if connected:
                consecutive_misses = 0
                has_slept = False  # allow future sleep after reconnect
            else:
                consecutive_misses += 1
                if consecutive_misses >= DISCONNECT_GRACE_CHECKS and not has_slept:
                    if no_sleep:
                        print("Device disconnected. (test mode: no sleep)")
                    else:
                        if FULL_SYSTEM_SLEEP:
                            print("Device disconnected. Sleeping system...")
                            sleep_system()
                        else:
                            print("Device disconnected. Turning off display...")
                            turn_off_display()
                    has_slept = True

            time.sleep(CHECK_INTERVAL_SEC)
            if max_checks is not None:
                checks_done += 1
                if checks_done >= max_checks:
                    break
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    if sys.platform != "win32":
        print("This tool is supported on Windows only.")
        sys.exit(1)
    main()
