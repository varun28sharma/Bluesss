"""
BlueLock - Optimized Bluetooth Proximity Lock
High-performance proximity monitoring for connected devices
"""

import asyncio
import json
import logging
import os
import platform
import subprocess
import time
import re
from datetime import datetime
from typing import Optional, Dict, List
from bleak import BleakScanner, BleakError
import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bluelock.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizedBlueLock:
    """Optimized BlueLock with performance improvements and better error handling"""
    
    def __init__(self):
        self.paired_devices = self._load_config()
        self.target_device: Optional[Dict] = None
        self.device_in_range = True
        self.system = platform.system().lower()
        self._scanner = None
        self._last_successful_scan = time.time()
        
        # Performance tracking
        self._scan_stats = {
            'total_scans': 0,
            'successful_detections': 0,
            'failed_scans': 0,
            'average_scan_time': 0
        }
        
    def _load_config(self) -> Dict:
        """Load device configuration with error handling"""
        try:
            if os.path.exists(settings.PAIRED_DEVICES_FILE):
                with open(settings.PAIRED_DEVICES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config: {e}")
        return {}
    
    def _save_config(self) -> bool:
        """Save device configuration with error handling"""
        try:
            with open(settings.PAIRED_DEVICES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.paired_devices, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def _get_connected_devices(self) -> List[Dict]:
        """Optimized device discovery for Windows"""
        if self.system != 'windows':
            logger.warning("Non-Windows platform detected. Limited functionality.")
            return []
        
        devices = []
        try:
            # Optimized PowerShell command for faster execution
            cmd = '''
            Get-PnpDevice -Class Bluetooth | 
            Where-Object {$_.Status -eq "OK" -and $_.InstanceId -like "*DEV_*"} | 
            Where-Object {$_.FriendlyName -notmatch "Avrcp|Service|Gateway|Generic|Profile|Enumerator|Protocol"} |
            Select-Object FriendlyName, InstanceId -First 20 |
            Format-Table -HideTableHeaders
            '''
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', cmd],
                capture_output=True, 
                text=True, 
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW  # Hide window
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\\n'):
                    if 'DEV_' in line and line.strip():
                        try:
                            parts = line.strip().split(None, 1)
                            if len(parts) >= 2:
                                device_name = parts[0]
                                instance_id = parts[1]
                                
                                # Extract MAC address more efficiently
                                mac_match = re.search(r'DEV_([A-F0-9]{12})', instance_id)
                                if mac_match:
                                    mac_hex = mac_match.group(1)
                                    mac_address = ':'.join(mac_hex[i:i+2] for i in range(0, 12, 2))
                                    
                                    devices.append({
                                        'name': device_name,
                                        'address': mac_address,
                                        'status': 'Connected'
                                    })
                        except Exception as e:
                            logger.debug(f"Error parsing device line: {e}")
                            
        except subprocess.TimeoutExpired:
            logger.warning("Device discovery timed out")
        except Exception as e:
            logger.error(f"Device discovery failed: {e}")
        
        return devices[:15]  # Limit to top 15 devices for performance
    
    async def _optimized_scan(self, target_address: str) -> Optional[int]:
        """Optimized Bluetooth scanning with better performance"""
        scan_start_time = time.time()
        found_rssi = None
        target_addr_lower = target_address.lower()
        
        def detection_callback(device, advertisement_data):
            nonlocal found_rssi
            if device.address.lower() == target_addr_lower:
                found_rssi = advertisement_data.rssi
        
        try:
            # Reuse scanner instance for better performance
            if not self._scanner:
                self._scanner = BleakScanner(detection_callback)
            else:
                self._scanner._callback = detection_callback
            
            await self._scanner.start()
            # Optimized scan time - shorter for better responsiveness
            await asyncio.sleep(1.8)
            await self._scanner.stop()
            
            # Update performance stats
            self._scan_stats['total_scans'] += 1
            scan_time = time.time() - scan_start_time
            self._scan_stats['average_scan_time'] = (
                (self._scan_stats['average_scan_time'] * (self._scan_stats['total_scans'] - 1) + scan_time) /
                self._scan_stats['total_scans']
            )
            
            if found_rssi is not None:
                self._scan_stats['successful_detections'] += 1
                self._last_successful_scan = time.time()
            else:
                self._scan_stats['failed_scans'] += 1
                
        except BleakError as e:
            logger.debug(f"Bluetooth scan error: {e}")
            self._scan_stats['failed_scans'] += 1
        except Exception as e:
            logger.error(f"Unexpected scan error: {e}")
            self._scan_stats['failed_scans'] += 1
        
        return found_rssi
    
    def _execute_system_action(self, action: str) -> bool:
        """Optimized system command execution"""
        commands = {
            'windows': {
                'lock': 'rundll32.exe user32.dll,LockWorkStation',
                'wake': 'powercfg /h off & powercfg /h on'
            },
            'darwin': {
                'lock': 'pmset displaysleepnow',
                'wake': 'caffeinate -u -t 1'
            },
            'linux': {
                'lock': 'loginctl lock-session',
                'wake': 'xset dpms force on'
            }
        }
        
        if self.system not in commands or action not in commands[self.system]:
            logger.warning(f"{action} not supported on {self.system}")
            return False
        
        try:
            cmd = commands[self.system][action]
            subprocess.run(
                cmd, 
                shell=True, 
                check=True, 
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if self.system == 'windows' else 0
            )
            logger.info(f"{action.title()} executed successfully")
            print(f"🔒 {action.title()} executed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to {action}: {e}")
            print(f"❌ Failed to {action}")
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"{action} command timed out")
            return False
    
    async def setup_device(self) -> bool:
        """Streamlined device setup"""
        # Check existing devices
        if self.paired_devices:
            print("📱 Previously configured devices:")
            for i, (addr, info) in enumerate(self.paired_devices.items(), 1):
                print(f"  {i}. {info['name']} ({addr[-8:]})")
            
            choice = input("\nUse existing device? (y/n): ").lower().strip()
            if choice == 'y':
                first_addr = list(self.paired_devices.keys())[0]
                self.target_device = {
                    'address': first_addr,
                    'name': self.paired_devices[first_addr]['name']
                }
                return True
        
        # Get connected devices
        print("🔍 Discovering connected devices...")
        devices = self._get_connected_devices()
        
        if not devices:
            print("❌ No connected devices found!")
            print("💡 Ensure your device is paired and connected via Bluetooth")
            return False
        
        # Display devices
        print(f"\n📋 Found {len(devices)} device(s):")
        print("─" * 60)
        for i, device in enumerate(devices, 1):
            print(f"{i:2}. {device['name']:<20} {device['address']}")
        print("─" * 60)
        
        # Device selection
        while True:
            try:
                choice = input(f"\nSelect device (1-{len(devices)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(devices):
                    selected = devices[idx]
                    
                    # Save configuration
                    device_info = {
                        'name': selected['name'],
                        'configured_at': datetime.now().isoformat(),
                        'status': 'Connected'
                    }
                    
                    self.paired_devices[selected['address']] = device_info
                    self.target_device = {
                        'address': selected['address'],
                        'name': selected['name']
                    }
                    
                    if self._save_config():
                        print(f"✅ Configured: {selected['name']}")
                        return True
                    else:
                        print("⚠️  Device configured but save failed")
                        return True
                else:
                    print("Invalid selection")
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Setup cancelled")
                return False
    
    async def monitor(self):
        """Optimized monitoring loop with performance tracking"""
        if not self.target_device:
            logger.error("No target device configured")
            return
        
        print(f"\n🎯 Monitoring: {self.target_device['name']}")
        print(f"📊 Threshold: {settings.RSSI_THRESHOLD} dBm | Interval: {settings.SCAN_INTERVAL}s")
        print("🟢 Monitoring active... (Ctrl+C to stop)\n")
        
        consecutive_misses = 0
        consecutive_hits = 0
        start_time = time.time()
        
        try:
            while True:
                rssi = await self._optimized_scan(self.target_device['address'])
                
                if rssi is not None:
                    # Device detected
                    consecutive_misses = 0
                    consecutive_hits += 1
                    
                    signal_strength = (
                        "🟢 Strong" if rssi > -50 else 
                        "🟡 Medium" if rssi > -70 else 
                        "🔴 Weak"
                    )
                    print(f"📶 {rssi:3} dBm {signal_strength}")
                    
                    # Wake if device was out of range
                    if not self.device_in_range and consecutive_hits >= 2:
                        self.device_in_range = True
                        print("🔓 Device back in range!")
                        if settings.ENABLE_WAKE:
                            self._execute_system_action('wake')
                
                else:
                    # Device not detected
                    consecutive_hits = 0
                    consecutive_misses += 1
                    print(f"❌ Not detected ({consecutive_misses})")
                    
                    # Lock after threshold
                    if (self.device_in_range and 
                        consecutive_misses >= settings.MIN_OUT_OF_RANGE_TIME // settings.SCAN_INTERVAL):
                        self.device_in_range = False
                        print("🔒 DEVICE OUT OF RANGE - LOCKING")
                        if settings.ENABLE_LOCK:
                            self._execute_system_action('lock')
                
                # Show stats every 10 scans
                if self._scan_stats['total_scans'] % 10 == 0:
                    success_rate = (self._scan_stats['successful_detections'] / 
                                  self._scan_stats['total_scans'] * 100)
                    runtime = (time.time() - start_time) / 60
                    print(f"📈 Stats: {success_rate:.1f}% success | {runtime:.1f}min runtime")
                
                await asyncio.sleep(settings.SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
            runtime = (time.time() - start_time) / 60
            print(f"📊 Final stats: {self._scan_stats['total_scans']} scans in {runtime:.1f}min")
        finally:
            if self._scanner:
                try:
                    await self._scanner.stop()
                except:
                    pass

async def main():
    """Optimized main function"""
    print("🔐 BlueLock - Optimized Proximity Monitor")
    print("=" * 50)
    
    blue_lock = OptimizedBlueLock()
    
    if not await blue_lock.setup_device():
        logger.error("Device setup failed")
        return
    
    await blue_lock.monitor()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 BlueLock stopped")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")