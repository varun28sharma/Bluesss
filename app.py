"""
BlueLock Web - Flask Web App for Bluetooth Screen Control
==========================================================
Access from any device on your network to monitor and control screen lock.
"""

from flask import Flask, render_template, jsonify, request
import subprocess
import json
import ctypes
import sys
import threading
import time

app = Flask(__name__)

# Global state
monitor_state = {
    "is_monitoring": False,
    "device_name": None,
    "device_id": None,
    "is_connected": False,
    "last_check": None,
    "screen_off": False
}

monitor_thread = None
stop_monitoring = False


def run_powershell(command):
    """Run PowerShell command and return output."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return result.stdout.strip()
    except:
        return ""


def get_all_bluetooth_devices():
    """Get all paired Bluetooth audio devices."""
    ps_audio = """
    Get-PnpDevice -Class AudioEndpoint |
    Select-Object FriendlyName, InstanceId, Status | ConvertTo-Json -Compress
    """
    output = run_powershell(ps_audio)
    
    if not output:
        return []
    
    try:
        data = json.loads(output)
        if isinstance(data, dict):
            data = [data]
        
        devices = []
        for d in data:
            name = (d.get("FriendlyName") or "").strip()
            instance_id = (d.get("InstanceId") or "").strip()
            status = (d.get("Status") or "").strip()
            
            if not name or not instance_id:
                continue
            
            name_lower = name.lower()
            
            # Skip built-in audio devices
            if "realtek" in name_lower:
                continue
            if "internal" in name_lower:
                continue
            if "speakers" in name_lower and "bluetooth" not in name_lower:
                continue
            if "microphone array" in name_lower:
                continue
            
            devices.append({
                "name": name,
                "instance_id": instance_id,
                "connected": status.upper() == "OK"
            })
            
        return devices
    except:
        return []


def is_device_connected(instance_id):
    """Check if device is still connected."""
    ps_command = f'(Get-PnpDevice -InstanceId "{instance_id}").Status'
    status = run_powershell(ps_command)
    return status.upper() == "OK"


def turn_off_screen():
    """Turn off the monitor."""
    if sys.platform == "win32":
        HWND_BROADCAST = 0xFFFF
        WM_SYSCOMMAND = 0x0112
        SC_MONITORPOWER = 0xF170
        ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2)
        return True
    return False


def monitor_loop():
    """Background monitoring loop."""
    global monitor_state, stop_monitoring
    
    miss_count = 0
    OUT_OF_RANGE_COUNT = 2
    
    while not stop_monitoring and monitor_state["is_monitoring"]:
        if monitor_state["device_id"]:
            connected = is_device_connected(monitor_state["device_id"])
            monitor_state["is_connected"] = connected
            monitor_state["last_check"] = time.strftime("%H:%M:%S")
            
            if connected:
                miss_count = 0
                monitor_state["screen_off"] = False
            else:
                miss_count += 1
                if miss_count >= OUT_OF_RANGE_COUNT and not monitor_state["screen_off"]:
                    turn_off_screen()
                    monitor_state["screen_off"] = True
        
        time.sleep(3)
    
    monitor_state["is_monitoring"] = False


# Routes
@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("index.html")


@app.route("/api/devices")
def api_devices():
    """Get list of Bluetooth devices."""
    devices = get_all_bluetooth_devices()
    return jsonify({"devices": devices})


@app.route("/api/status")
def api_status():
    """Get current monitoring status."""
    return jsonify(monitor_state)


@app.route("/api/start", methods=["POST"])
def api_start():
    """Start monitoring a device."""
    global monitor_thread, stop_monitoring, monitor_state
    
    data = request.get_json()
    device_name = data.get("device_name")
    device_id = data.get("device_id")
    
    if not device_id:
        return jsonify({"error": "No device selected"}), 400
    
    # Stop existing monitoring
    stop_monitoring = True
    if monitor_thread and monitor_thread.is_alive():
        monitor_thread.join(timeout=5)
    
    # Start new monitoring
    stop_monitoring = False
    monitor_state["is_monitoring"] = True
    monitor_state["device_name"] = device_name
    monitor_state["device_id"] = device_id
    monitor_state["is_connected"] = is_device_connected(device_id)
    monitor_state["screen_off"] = False
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    
    return jsonify({"success": True, "message": f"Monitoring {device_name}"})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """Stop monitoring."""
    global stop_monitoring, monitor_state
    
    stop_monitoring = True
    monitor_state["is_monitoring"] = False
    monitor_state["device_name"] = None
    monitor_state["device_id"] = None
    
    return jsonify({"success": True, "message": "Monitoring stopped"})


@app.route("/api/screen-off", methods=["POST"])
def api_screen_off():
    """Manually turn off screen."""
    success = turn_off_screen()
    return jsonify({"success": success})


if __name__ == "__main__":
    # Get local IP for network access
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("=" * 50)
    print("🔵 BlueLock Web Server")
    print("=" * 50)
    print(f"Local:   http://127.0.0.1:5000")
    print(f"Network: http://{local_ip}:5000")
    print("=" * 50)
    
    app.run(host="0.0.0.0", port=5000, debug=False)
