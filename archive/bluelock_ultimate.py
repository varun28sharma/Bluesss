"""
BlueLock Ultimate - Perfect for connected devices with enhanced GUI
Automatically detects connected devices and provides beautiful interface
"""

import asyncio
import json
import time
import subprocess
import re
import sys
import os
from typing import Dict, List, Optional
from bleak import BleakScanner
import settings

class UltimateBlueLock:
    def __init__(self):
        self.connected_devices = {}
        self.target_device = None
        self.device_in_range = False
        self.stats = {
            'scans': 0,
            'detections': 0,
            'start_time': time.time()
        }
        
    def get_active_devices(self) -> List[Dict]:
        """Get currently active/connected Bluetooth devices using simple method"""
        print("🔍 Scanning for connected devices...")
        
        devices = []
        try:
            # Simple and fast PowerShell command
            cmd = '''
            Get-PnpDevice -Class Bluetooth | Where-Object {
                $_.Status -eq "OK" -and 
                $_.FriendlyName -ne $null -and
                $_.FriendlyName -notmatch "Service|Transport|Profile|Protocol|Gateway|Generic|Microsoft|Enumerator|Avrcp"
            } | ForEach-Object {
                $name = $_.FriendlyName
                $instanceId = $_.InstanceId
                if ($instanceId -match "DEV_([A-F0-9]{12})") {
                    $macHex = $matches[1]
                    $mac = ($macHex -replace "(..)","$1:").TrimEnd(":")
                    Write-Output "$name|$mac"
                }
            }
            '''
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', cmd],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and '|' in line:
                        try:
                            name, address = line.strip().split('|', 1)
                            if name and address and len(address) == 17:
                                priority = self._get_priority(name)
                                devices.append({
                                    'name': name.strip(),
                                    'address': address.strip().upper(),
                                    'priority': priority,
                                    'type': self._get_device_type(name.strip())
                                })
                        except ValueError:
                            continue
            
            # Sort by priority (audio devices first)
            devices.sort(key=lambda x: x['priority'], reverse=True)
            
        except Exception as e:
            print(f"Error getting devices: {e}")
        
        print(f"✅ Found {len(devices)} connected devices")
        return devices
    
    def _get_priority(self, name: str) -> int:
        """Device priority for auto-selection"""
        name_lower = name.lower()
        if any(word in name_lower for word in ['buds', 'airpods', 'headphone', 'earphone']):
            return 10
        if any(word in name_lower for word in ['audio', 'sound', 'speaker']):
            return 8
        if any(word in name_lower for word in ['watch', 'band']):
            return 7
        if any(word in name_lower for word in ['mouse', 'keyboard']):
            return 5
        if any(word in name_lower for word in ['phone', 'mobile']):
            return 3
        return 1
    
    def _get_device_type(self, name: str) -> str:
        """Get device type for display"""
        name_lower = name.lower()
        if any(word in name_lower for word in ['buds', 'airpods', 'headphone', 'earphone']):
            return "🎵 Audio"
        if any(word in name_lower for word in ['watch', 'band']):
            return "⌚ Watch"
        if any(word in name_lower for word in ['mouse']):
            return "🖱️ Mouse"
        if any(word in name_lower for word in ['phone', 'mobile']):
            return "📱 Phone"
        if any(word in name_lower for word in ['speaker']):
            return "🔊 Speaker"
        return "📟 Device"
    
    def select_device_interactive(self, devices: List[Dict]) -> Optional[Dict]:
        """Interactive device selection with better UI"""
        if not devices:
            return None
        
        print("\n" + "="*70)
        print("📱 CONNECTED BLUETOOTH DEVICES")
        print("="*70)
        
        for i, device in enumerate(devices, 1):
            print(f"{i:2d}. {device['type']} {device['name']:<35}")
            print(f"    📍 {device['address']}")
            print()
        
        print("="*70)
        print("💡 Tip: Audio devices (headphones/earbuds) work best for proximity detection")
        print()
        
        while True:
            try:
                choice = input(f"Select device (1-{len(devices)}) or 'auto' for best device: ").strip().lower()
                
                if choice == 'auto':
                    selected = devices[0]  # Highest priority
                    print(f"🎯 Auto-selected: {selected['name']}")
                    return selected
                
                idx = int(choice) - 1
                if 0 <= idx < len(devices):
                    return devices[idx]
                else:
                    print("❌ Invalid selection!")
                    
            except ValueError:
                print("❌ Please enter a number or 'auto'!")
            except KeyboardInterrupt:
                print("\n❌ Cancelled")
                return None
    
    async def smart_scan(self, address: str, timeout: float = 4.0) -> Optional[float]:
        """Smart scanning for connected devices"""
        self.stats['scans'] += 1
        
        try:
            # Method 1: Quick discovery
            devices = await BleakScanner.discover(timeout=timeout/2, return_adv=True)
            for device, adv_data in devices.items():
                if device.address.upper() == address.upper():
                    self.stats['detections'] += 1
                    return adv_data.rssi
            
            # Method 2: Callback scan
            found_rssi = None
            def callback(device, adv_data):
                nonlocal found_rssi
                if device.address.upper() == address.upper():
                    found_rssi = adv_data.rssi
            
            scanner = BleakScanner(callback)
            await scanner.start()
            await asyncio.sleep(timeout/2)
            await scanner.stop()
            
            if found_rssi:
                self.stats['detections'] += 1
                return found_rssi
                
        except Exception as e:
            pass  # Silent fail for cleaner output
        
        return None
    
    def lock_system(self):
        """Lock the system"""
        try:
            if settings.ENABLE_LOCK:
                subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], 
                             creationflags=subprocess.CREATE_NO_WINDOW)
                print("🔒 SYSTEM LOCKED")
        except Exception:
            pass
    
    def wake_system(self):
        """Wake the system"""
        try:
            if settings.ENABLE_WAKE:
                subprocess.run(['powercfg', '/requests'], 
                             creationflags=subprocess.CREATE_NO_WINDOW)
                print("🔓 SYSTEM UNLOCKED")
        except Exception:
            pass
    
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        runtime = time.time() - self.stats['start_time']
        success_rate = (self.stats['detections'] / max(1, self.stats['scans'])) * 100
        return {
            'runtime_min': runtime / 60,
            'scans': self.stats['scans'],
            'detections': self.stats['detections'],
            'success_rate': success_rate
        }
    
    async def monitor_device(self, device: Dict):
        """Enhanced device monitoring with beautiful output"""
        target_address = device['address']
        target_name = device['name']
        
        print("\n" + "="*80)
        print("🔒 BLUELOCK ULTIMATE - PROXIMITY MONITORING")
        print("="*80)
        print(f"📱 Device: {device['type']} {target_name}")
        print(f"📍 Address: {target_address}")
        print(f"⚙️  Scan Interval: {settings.SCAN_INTERVAL}s")
        print(f"📊 Lock Threshold: {settings.RSSI_THRESHOLD} dBm")
        print("="*80)
        print("🟢 MONITORING ACTIVE - Press Ctrl+C to stop")
        print("="*80)
        print()
        
        consecutive_misses = 0
        consecutive_hits = 0
        last_rssi = None
        
        try:
            while True:
                rssi = await self.smart_scan(target_address)
                
                if rssi is not None:
                    # Device detected
                    consecutive_misses = 0
                    consecutive_hits += 1
                    last_rssi = rssi
                    
                    # Signal strength visualization
                    if rssi >= -50:
                        strength = "🟢 EXCELLENT"
                        bars = "████████████"
                    elif rssi >= -60:
                        strength = "🟢 STRONG"
                        bars = "█████████░░░"
                    elif rssi >= -70:
                        strength = "🟡 GOOD"
                        bars = "██████░░░░░░"
                    elif rssi >= -80:
                        strength = "🟠 WEAK"
                        bars = "███░░░░░░░░░"
                    else:
                        strength = "🔴 VERY WEAK"
                        bars = "█░░░░░░░░░░░"
                    
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] 📶 {rssi:3}dBm {bars} {strength} | Hits: {consecutive_hits}")
                    
                    # Device came back in range
                    if not self.device_in_range and consecutive_hits >= 2:
                        self.device_in_range = True
                        print("🔓 ▶ DEVICE BACK IN RANGE - UNLOCKING SYSTEM")
                        self.wake_system()
                
                else:
                    # Device not detected
                    consecutive_hits = 0
                    consecutive_misses += 1
                    
                    timestamp = time.strftime("%H:%M:%S")
                    last_info = f" (Last: {last_rssi}dBm)" if last_rssi else ""
                    print(f"[{timestamp}] ❌ Not detected ({consecutive_misses}){last_info}")
                    
                    # Check if should lock
                    required_misses = max(2, settings.MIN_OUT_OF_RANGE_TIME // settings.SCAN_INTERVAL)
                    if self.device_in_range and consecutive_misses >= required_misses:
                        self.device_in_range = False
                        print("🔒 ▶ DEVICE OUT OF RANGE - LOCKING SYSTEM")
                        self.lock_system()
                
                # Show stats every 20 scans
                if self.stats['scans'] % 20 == 0:
                    stats = self.get_stats()
                    print(f"📊 Runtime: {stats['runtime_min']:.1f}min | Success: {stats['success_rate']:.1f}% | Scans: {stats['scans']}")
                
                await asyncio.sleep(settings.SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n⏹️  MONITORING STOPPED")
            stats = self.get_stats()
            print(f"📊 Final Stats: {stats['scans']} scans, {stats['success_rate']:.1f}% success, {stats['runtime_min']:.1f}min runtime")

async def main():
    """Main application"""
    bluelock = UltimateBlueLock()
    
    print("🔒 BlueLock Ultimate - Connected Device Monitor")
    print("Automatically detects and monitors your connected Bluetooth devices")
    print()
    
    # Get connected devices
    devices = bluelock.get_active_devices()
    
    if not devices:
        print("❌ No connected Bluetooth devices found!")
        print()
        print("💡 Please ensure:")
        print("   • Your Bluetooth device is turned ON")
        print("   • Device is connected (not just paired) to Windows")
        print("   • Device is within range of your laptop")
        print()
        print("📱 Recommended devices:")
        print("   • Bluetooth headphones/earbuds (work best)")
        print("   • Smartwatches")
        print("   • Bluetooth speakers")
        return
    
    # Select device
    selected_device = bluelock.select_device_interactive(devices)
    
    if not selected_device:
        print("❌ No device selected")
        return
    
    # Save configuration
    config = {
        'target_device': selected_device,
        'saved_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        with open('bluelock_ultimate_config.json', 'w') as f:
            json.dump(config, f, indent=2)
    except:
        pass  # Don't fail if can't save
    
    # Start monitoring
    await bluelock.monitor_device(selected_device)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Application stopped")
    except Exception as e:
        print(f"❌ Error: {e}")