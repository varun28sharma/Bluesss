"""
BlueLock Simple - Screen OFF when Bluetooth device goes out of range
=====================================================================
- AUTO-DETECTS connected Bluetooth device (no selection needed)
- If no device is connected → exits immediately
- If device is connected → monitors it
- Screen turns OFF when device disconnects/goes out of range

Usage: python bluelock_simple.py
"""

import subprocess
import json
import time
import ctypes
import sys
import os


# Settings
CHECK_INTERVAL = 3.0  # Check every 3 seconds
OUT_OF_RANGE_COUNT = 2  # Wait for 2 consecutive misses before turning off screen (~6 sec)


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


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


def get_connected_device():
    """Find the first CONNECTED Bluetooth audio device (Status = OK)."""
    ps_command = """
    Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq 'OK'} |
    Select-Object FriendlyName, InstanceId, Status | ConvertTo-Json -Compress
    """
    output = run_powershell(ps_command)
    
    if not output:
        return None
    
    try:
        data = json.loads(output)
        if isinstance(data, dict):
            data = [data]
        
        for d in data:
            name = (d.get("FriendlyName") or "").strip()
            instance_id = (d.get("InstanceId") or "").strip()
            
            # Skip system/adapter entries - only want actual devices
            if not name or not instance_id:
                continue
            if "adapter" in name.lower():
                continue
            if "enumerator" in name.lower():
                continue
            if "radio" in name.lower():
                continue
            if "mediatek" in name.lower():
                continue
            if "intel" in name.lower():
                continue
            if "realtek" in name.lower():
                continue
            if "broadcom" in name.lower():
                continue
            if "qualcomm" in name.lower():
                continue
            
            # Found a connected device!
            return {"name": name, "instance_id": instance_id}
        
        return None
    except:
        return None


def is_device_connected(instance_id):
    """Check if device is still connected (Status = OK)."""
    ps_command = f'(Get-PnpDevice -InstanceId "{instance_id}").Status'
    status = run_powershell(ps_command)
    return status.upper() == "OK"


def turn_off_screen():
    """Turn off the monitor."""
    HWND_BROADCAST = 0xFFFF
    WM_SYSCOMMAND = 0x0112
    SC_MONITORPOWER = 0xF170
    ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2)


def monitor_device(device):
    """Monitor the device until it disconnects."""
    name = device["name"]
    instance_id = device["instance_id"]
    
    print()
    print("=" * 60)
    print(f"🎯 Monitoring: {name}")
    print("=" * 60)
    print()
    print("📱 CONNECTED    → Screen stays ON")
    print("📴 DISCONNECTED → Screen turns OFF")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 60)
    print()
    
    miss_count = 0
    screen_off = False
    
    try:
        while True:
            connected = is_device_connected(instance_id)
            
            if connected:
                miss_count = 0
                if screen_off:
                    print(f"[{time.strftime('%H:%M:%S')}] 🔵 Device reconnected!")
                    screen_off = False
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] ✅ Connected - Screen ON", end="          \r")
            else:
                miss_count += 1
                print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Not connected ({miss_count}/{OUT_OF_RANGE_COUNT})        ")
                
                if miss_count >= OUT_OF_RANGE_COUNT and not screen_off:
                    print(f"[{time.strftime('%H:%M:%S')}] 😴 Device disconnected - Turning OFF screen...")
                    turn_off_screen()
                    screen_off = True
                    print(f"[{time.strftime('%H:%M:%S')}] 💤 Screen OFF - Move mouse to wake")
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n👋 Stopped. Goodbye!")


def main():
    if sys.platform != "win32":
        print("This program only works on Windows.")
        sys.exit(1)
    
    clear_screen()
    print("=" * 60)
    print("🔵 BlueLock Simple - Auto Screen Control")
    print("=" * 60)
    print()
    print("🔍 Looking for connected Bluetooth device...")
    
    # Auto-detect connected device
    device = get_connected_device()
    
    if not device:
        print()
        print("❌ No Bluetooth device is currently CONNECTED!")
        print()
        print("Please connect your Bluetooth device first, then run again.")
        print()
        sys.exit(0)
    
    print(f"✅ Found: {device['name']}")
    
    # Start monitoring
    monitor_device(device)


if __name__ == "__main__":
    main()
