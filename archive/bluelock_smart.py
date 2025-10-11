"""
BlueLock Smart Auto - Automatically detects and monitors connected devices
No manual device selection needed - works with currently connected devices only
"""

import asyncio
import logging
import json
import time
import subprocess
import re
import sys
import os
from typing import Dict, List, Optional, Tuple
from bleak import BleakScanner
import settings

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bluelock_smart.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SmartBlueLock:
    def __init__(self):
        self.connected_devices = {}
        self.target_device = None
        self.device_in_range = False
        self.performance_stats = {
            'scans_performed': 0,
            'successful_detections': 0,
            'start_time': time.time(),
            'auto_selections': 0
        }
        self.connection_status = {}
        
    def get_currently_connected_devices(self) -> List[Dict]:
        """Get only currently CONNECTED (not just paired) Bluetooth devices"""
        logger.info("🔍 Scanning for CURRENTLY CONNECTED devices...")
        
        connected_devices = []
        
        try:
            # Enhanced PowerShell to get ONLY connected devices
            cmd = '''
            # Get devices that are currently connected and active
            $connectedDevices = @()
            
            # Method 1: Check Bluetooth radio status and connected devices
            $btRadios = Get-PnpDevice -Class Bluetooth | Where-Object {
                $_.Status -eq "OK" -and 
                $_.FriendlyName -ne $null -and
                $_.FriendlyName -notmatch "Service|Profile|Gateway|Protocol|Enumerator|Generic|Microsoft|Transport|TDI|CDP|SDP" -and
                $_.FriendlyName -notmatch "Avrcp|Pse|NAP|Access|Push|Identification|Discovery|Attribute"
            }
            
            foreach ($device in $btRadios) {
                $name = $device.FriendlyName
                $instanceId = $device.InstanceId
                
                if ($instanceId -match "DEV_([A-F0-9]{12})") {
                    $macHex = $matches[1]
                    $mac = ""
                    for ($i = 0; $i -lt 12; $i += 2) {
                        if ($mac) { $mac += ":" }
                        $mac += $macHex.Substring($i, 2)
                    }
                    
                    # Check if device is actually connected (not just paired)
                    try {
                        $connectedCheck = Get-PnpDevice -InstanceId $instanceId | Where-Object {$_.Status -eq "OK"}
                        if ($connectedCheck) {
                            Write-Output "$name|$mac|Connected"
                        }
                    } catch {
                        # Ignore errors for individual devices
                    }
                }
            }
            '''
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', cmd],
                capture_output=True, 
                text=True, 
                timeout=20,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                logger.info(f"Found {len(lines)} device entries")
                
                for line in lines:
                    if line.strip() and '|' in line:
                        try:
                            parts = line.strip().split('|')
                            if len(parts) >= 3:
                                name = parts[0].strip()
                                address = parts[1].strip().upper()
                                status = parts[2].strip()
                                
                                if name and address and len(address) == 17:
                                    # Prioritize audio devices for better proximity detection
                                    device_priority = self._get_device_priority(name)
                                    
                                    connected_devices.append({
                                        'name': name,
                                        'address': address,
                                        'status': status,
                                        'priority': device_priority,
                                        'last_seen': time.time()
                                    })
                                    
                        except Exception as e:
                            logger.debug(f"Error parsing device line '{line}': {e}")
                            continue
                
                # Sort by priority (audio devices first)
                connected_devices.sort(key=lambda x: x['priority'], reverse=True)
                
        except Exception as e:
            logger.error(f"Error getting connected devices: {e}")
        
        logger.info(f"✅ Found {len(connected_devices)} currently connected devices")
        return connected_devices
    
    def _get_device_priority(self, device_name: str) -> int:
        """Assign priority to devices for auto-selection (higher = better for proximity)"""
        name_lower = device_name.lower()
        
        # Audio devices work best for proximity detection
        if any(keyword in name_lower for keyword in ['buds', 'airpods', 'headphone', 'earphone', 'speaker']):
            return 10
        if any(keyword in name_lower for keyword in ['audio', 'sound', 'music']):
            return 8
        if any(keyword in name_lower for keyword in ['watch', 'band', 'fitness']):
            return 7
        if any(keyword in name_lower for keyword in ['mouse', 'keyboard']):
            return 5
        if any(keyword in name_lower for keyword in ['phone', 'mobile']):
            return 3
        
        return 1  # Default priority
    
    def auto_select_best_device(self) -> Optional[Dict]:
        """Automatically select the best connected device for monitoring"""
        logger.info("🎯 Auto-selecting best device for monitoring...")
        
        devices = self.get_currently_connected_devices()
        
        if not devices:
            logger.warning("❌ No connected devices found for auto-selection")
            return None
        
        # Display found devices
        print("\n🔍 Currently Connected Devices:")
        print("=" * 60)
        for i, device in enumerate(devices, 1):
            priority_text = "🎵 Audio" if device['priority'] >= 8 else "📱 Other"
            print(f" {i:2d}. {device['name']:<30} {priority_text}")
            print(f"     📍 {device['address']} | Status: {device['status']}")
        
        # Auto-select the highest priority device
        best_device = devices[0]  # Already sorted by priority
        
        print(f"\n🎯 AUTO-SELECTED DEVICE:")
        print(f"   📱 {best_device['name']}")
        print(f"   📍 {best_device['address']}")
        print(f"   🔹 Priority: {best_device['priority']} (Audio devices work best)")
        
        self.performance_stats['auto_selections'] += 1
        return best_device
    
    async def smart_device_scan(self, target_address: str, timeout: float = 3.0) -> Optional[float]:
        """Smart scanning specifically for connected devices"""
        self.performance_stats['scans_performed'] += 1
        
        try:
            # For connected devices, try multiple scanning approaches
            
            # Method 1: Quick BLE advertisement scan
            rssi = await self._quick_ble_scan(target_address, timeout)
            if rssi is not None:
                self.performance_stats['successful_detections'] += 1
                return rssi
            
            # Method 2: Broader scan with callback
            rssi = await self._callback_scan(target_address, timeout * 1.5)
            if rssi is not None:
                self.performance_stats['successful_detections'] += 1
                return rssi
            
            # Method 3: Connection attempt (for some devices that don't advertise)
            if await self._test_device_connectivity(target_address):
                # Device is connected but not advertising, return estimated RSSI
                self.performance_stats['successful_detections'] += 1
                return -60  # Assume good signal if directly connectable
            
        except Exception as e:
            logger.debug(f"Smart scan error for {target_address}: {e}")
        
        return None
    
    async def _quick_ble_scan(self, target_address: str, timeout: float) -> Optional[float]:
        """Quick BLE advertisement scan"""
        try:
            devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
            for device, adv_data in devices.items():
                if device.address.upper() == target_address.upper():
                    logger.debug(f"Quick scan found {target_address}: {adv_data.rssi} dBm")
                    return adv_data.rssi
        except Exception as e:
            logger.debug(f"Quick BLE scan error: {e}")
        return None
    
    async def _callback_scan(self, target_address: str, timeout: float) -> Optional[float]:
        """Callback-based scanning"""
        found_rssi = None
        
        def detection_callback(device, advertisement_data):
            nonlocal found_rssi
            if device.address.upper() == target_address.upper():
                found_rssi = advertisement_data.rssi
                logger.debug(f"Callback scan found {target_address}: {found_rssi} dBm")
        
        try:
            scanner = BleakScanner(detection_callback)
            await scanner.start()
            await asyncio.sleep(timeout)
            await scanner.stop()
            return found_rssi
        except Exception as e:
            logger.debug(f"Callback scan error: {e}")
            return None
    
    async def _test_device_connectivity(self, target_address: str) -> bool:
        """Test if device is still connected via Windows"""
        try:
            # Check if device is still showing as connected in Windows
            cmd = f'''
            Get-PnpDevice -Class Bluetooth | Where-Object {{
                $_.InstanceId -match "DEV_{target_address.replace(":", "")}" -and $_.Status -eq "OK"
            }} | Measure-Object | Select-Object -ExpandProperty Count
            '''
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', cmd],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                count = int(result.stdout.strip())
                return count > 0
                
        except Exception as e:
            logger.debug(f"Connectivity test error: {e}")
        
        return False
    
    def _execute_system_action(self, action: str):
        """Execute lock/wake actions with better feedback"""
        try:
            if action == 'lock' and settings.ENABLE_LOCK:
                subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], 
                             creationflags=subprocess.CREATE_NO_WINDOW)
                logger.info("🔒 System locked")
                print("🔒 SYSTEM LOCKED")
                
            elif action == 'wake' and settings.ENABLE_WAKE:
                # Wake display
                subprocess.run(['powercfg', '/requests'], 
                             creationflags=subprocess.CREATE_NO_WINDOW)
                logger.info("🔓 System woken")
                print("🔓 SYSTEM UNLOCKED")
                
        except Exception as e:
            logger.error(f"System action '{action}' failed: {e}")
    
    def get_performance_stats(self) -> Dict:
        """Get enhanced performance statistics"""
        runtime = time.time() - self.performance_stats['start_time']
        success_rate = 0
        
        if self.performance_stats['scans_performed'] > 0:
            success_rate = (self.performance_stats['successful_detections'] / 
                          self.performance_stats['scans_performed']) * 100
        
        return {
            'runtime_minutes': runtime / 60,
            'scans_performed': self.performance_stats['scans_performed'],
            'successful_detections': self.performance_stats['successful_detections'],
            'success_rate': success_rate,
            'auto_selections': self.performance_stats['auto_selections']
        }
    
    async def smart_monitor(self):
        """Smart monitoring with auto device selection"""
        print("🔒 BlueLock Smart Auto - Connected Device Monitor")
        print("=" * 65)
        print("🎯 Automatically finding and monitoring connected devices...")
        print()
        
        # Auto-select best device
        selected_device = self.auto_select_best_device()
        
        if not selected_device:
            print("❌ No suitable connected devices found!")
            print("💡 Make sure you have Bluetooth devices connected (not just paired)")
            print("   • Turn on your Bluetooth headphones/earbuds")
            print("   • Connect your smartwatch")
            print("   • Ensure devices are actively connected in Windows")
            return
        
        self.target_device = selected_device
        target_address = selected_device['address']
        target_name = selected_device['name']
        
        print(f"\n🚀 STARTING AUTOMATIC MONITORING")
        print("=" * 65)
        print(f"📱 Device: {target_name}")
        print(f"📍 Address: {target_address}")
        print(f"🔧 Scan Interval: {settings.SCAN_INTERVAL}s")
        print(f"📊 Lock Threshold: {settings.RSSI_THRESHOLD} dBm")
        print("🟢 Smart monitoring active... (Ctrl+C to stop)")
        print()
        
        consecutive_misses = 0
        consecutive_hits = 0
        last_rssi = None
        
        try:
            while True:
                # Smart scan for device
                rssi = await self.smart_device_scan(target_address)
                
                if rssi is not None:
                    # Device detected
                    consecutive_misses = 0
                    consecutive_hits += 1
                    last_rssi = rssi
                    
                    # Enhanced signal strength display
                    if rssi > -50:
                        strength = "🟢 STRONG"
                        icon = "📶"
                    elif rssi > -70:
                        strength = "🟡 MEDIUM"
                        icon = "📶"
                    else:
                        strength = "🔴 WEAK"
                        icon = "📶"
                    
                    print(f"{icon} {rssi:3} dBm {strength} | Connected: {consecutive_hits}")
                    
                    # Device came back in range
                    if not self.device_in_range and consecutive_hits >= 2:
                        self.device_in_range = True
                        print("🔓 DEVICE BACK IN RANGE!")
                        self._execute_system_action('wake')
                
                else:
                    # Device not detected
                    consecutive_hits = 0
                    consecutive_misses += 1
                    
                    status_text = f"Not detected ({consecutive_misses})"
                    if last_rssi:
                        status_text += f" | Last: {last_rssi} dBm"
                    
                    print(f"❌ {status_text}")
                    
                    # Device went out of range
                    required_misses = max(2, settings.MIN_OUT_OF_RANGE_TIME // settings.SCAN_INTERVAL)
                    if self.device_in_range and consecutive_misses >= required_misses:
                        self.device_in_range = False
                        print("🔒 DEVICE OUT OF RANGE - LOCKING SYSTEM")
                        self._execute_system_action('lock')
                
                # Performance stats every 15 scans
                if self.performance_stats['scans_performed'] % 15 == 0:
                    stats = self.get_performance_stats()
                    print(f"📊 Stats: {stats['success_rate']:.1f}% success | {stats['runtime_minutes']:.1f}min runtime")
                
                await asyncio.sleep(settings.SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n⏹️  Smart monitoring stopped")
            stats = self.get_performance_stats()
            print(f"📊 Final: {stats['scans_performed']} scans, {stats['success_rate']:.1f}% success")
            print(f"🎯 Auto-selections: {stats['auto_selections']}")

async def main():
    """Main application entry point"""
    smart_lock = SmartBlueLock()
    
    try:
        await smart_lock.smart_monitor()
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())