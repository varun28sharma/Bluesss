"""
BlueLock - Enhanced Bluetooth Proximity Monitor
Fixed connectivity issues with improved device detection
"""

import asyncio
import logging
import json
import time
import subprocess
import re
import sys
import os
from typing import Dict, List, Optional
from bleak import BleakScanner
import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bluelock.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnhancedBlueLock:
    def __init__(self):
        self.target_device = None
        self.paired_devices = {}
        self.device_in_range = False
        self.scanner = None
        self.performance_stats = {
            'scans_performed': 0,
            'successful_detections': 0,
            'start_time': time.time()
        }
        
        # Load existing configuration
        self._load_config()
        
    def _load_config(self):
        """Load device configuration from multiple sources"""
        config_files = ['enhanced_bluelock_config.json', 'bluelock_config.json']
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        
                    if 'target_device' in config:
                        self.target_device = config['target_device']
                    if 'paired_devices' in config:
                        self.paired_devices = config['paired_devices']
                        
                    logger.info(f"Configuration loaded from {config_file}")
                    return
                except Exception as e:
                    logger.error(f"Error loading config from {config_file}: {e}")
        
        logger.info("No existing configuration found")
    
    def _save_config(self):
        """Save current configuration"""
        config = {
            'target_device': self.target_device,
            'paired_devices': self.paired_devices,
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            with open('bluelock_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def get_enhanced_device_list(self):
        """Enhanced device detection using multiple methods"""
        devices = {}
        
        # Method 1: Get Windows paired devices
        logger.info("Scanning for paired devices...")
        paired_devices = self._get_windows_paired_devices()
        for mac, info in paired_devices.items():
            devices[mac] = info
        
        logger.info(f"Found {len(paired_devices)} paired devices")
        return list(devices.values())
    
    def _get_windows_paired_devices(self):
        """Enhanced Windows paired device detection"""
        devices = {}
        
        try:
            # Enhanced PowerShell command
            cmd = '''
            Get-PnpDevice -Class Bluetooth | 
            Where-Object {$_.Status -eq "OK" -and $_.FriendlyName -ne $null} | 
            Where-Object {$_.FriendlyName -notmatch "Microsoft|Generic|Profile|Service|Gateway|Protocol|Enumerator"} |
            ForEach-Object {
                $name = $_.FriendlyName
                $instanceId = $_.InstanceId
                if ($instanceId -match "DEV_([A-F0-9]{12})") {
                    $macHex = $matches[1]
                    $mac = ""
                    for ($i = 0; $i -lt 12; $i += 2) {
                        if ($mac) { $mac += ":" }
                        $mac += $macHex.Substring($i, 2)
                    }
                    Write-Output "$name|$mac"
                }
            }
            '''
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', cmd],
                capture_output=True, 
                text=True, 
                timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and '|' in line:
                        try:
                            name, address = line.strip().split('|', 1)
                            name = name.strip()
                            address = address.strip().upper()
                            
                            if name and address and len(address) == 17:
                                devices[address] = {
                                    'name': name,
                                    'address': address,
                                    'status': 'Paired',
                                    'method': 'Windows Registry'
                                }
                        except ValueError:
                            continue
            else:
                logger.error(f"PowerShell command failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error getting Windows paired devices: {e}")
        
        return devices

    async def enhanced_scan_for_device(self, target_address: str, timeout: float = 5.0) -> Optional[float]:
        """Enhanced device scanning with better error handling"""
        self.performance_stats['scans_performed'] += 1
        
        try:
            # First, try a quick targeted scan
            detected_rssi = await self._quick_targeted_scan(target_address, timeout)
            
            if detected_rssi is not None:
                self.performance_stats['successful_detections'] += 1
                return detected_rssi
            
            # If quick scan fails, try a broader scan
            logger.debug(f"Quick scan failed for {target_address}, trying broader scan...")
            return await self._broader_device_scan(target_address, timeout * 2)
            
        except Exception as e:
            logger.error(f"Enhanced scan error: {e}")
            return None

    async def _quick_targeted_scan(self, target_address: str, timeout: float) -> Optional[float]:
        """Quick targeted scan for specific device"""
        try:
            devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
            
            for device, adv_data in devices.items():
                if device.address.upper() == target_address.upper():
                    logger.debug(f"Found target device {target_address} with RSSI {adv_data.rssi}")
                    return adv_data.rssi
                    
        except Exception as e:
            logger.debug(f"Quick scan error: {e}")
        
        return None

    async def _broader_device_scan(self, target_address: str, timeout: float) -> Optional[float]:
        """Broader scan as fallback method"""
        found_rssi = None
        
        def detection_callback(device, advertisement_data):
            nonlocal found_rssi
            if device.address.upper() == target_address.upper():
                found_rssi = advertisement_data.rssi
                logger.debug(f"Broader scan found {target_address} with RSSI {found_rssi}")
        
        try:
            scanner = BleakScanner(detection_callback)
            await scanner.start()
            await asyncio.sleep(timeout)
            await scanner.stop()
            
            if found_rssi is not None:
                self.performance_stats['successful_detections'] += 1
            
            return found_rssi
            
        except Exception as e:
            logger.debug(f"Broader scan error: {e}")
            return None

    def _execute_system_action(self, action: str):
        """Execute system lock/wake actions"""
        try:
            if action == 'lock' and settings.ENABLE_LOCK:
                if sys.platform == 'win32':
                    subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], 
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                    logger.info("Lock executed successfully")
                    print("🔒 Lock executed")
                    
            elif action == 'wake' and settings.ENABLE_WAKE:
                if sys.platform == 'win32':
                    # Wake up the display
                    subprocess.run(['powercfg', '/requests'], 
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                    logger.info("Wake executed successfully")
                    print("🔓 Wake executed")
                    
        except Exception as e:
            logger.error(f"System action '{action}' failed: {e}")

    def get_performance_stats(self):
        """Get current performance statistics"""
        runtime = time.time() - self.performance_stats['start_time']
        success_rate = 0
        
        if self.performance_stats['scans_performed'] > 0:
            success_rate = (self.performance_stats['successful_detections'] / 
                          self.performance_stats['scans_performed']) * 100
        
        return {
            'runtime_minutes': runtime / 60,
            'scans_performed': self.performance_stats['scans_performed'],
            'successful_detections': self.performance_stats['successful_detections'],
            'success_rate': success_rate
        }

    async def monitor_device(self):
        """Enhanced device monitoring loop"""
        if not self.target_device:
            print("❌ No target device configured!")
            return
        
        target_address = self.target_device['address']
        target_name = self.target_device['name']
        
        print(f"🎯 Monitoring: {target_name}")
        print(f"📊 Address: {target_address}")
        print(f"📊 Threshold: {settings.RSSI_THRESHOLD} dBm | Interval: {settings.SCAN_INTERVAL}s")
        print("🟢 Enhanced monitoring active... (Ctrl+C to stop)")
        print()
        
        consecutive_misses = 0
        consecutive_hits = 0
        
        try:
            while True:
                # Scan for device
                rssi = await self.enhanced_scan_for_device(target_address)
                
                if rssi is not None:
                    # Device detected
                    consecutive_misses = 0
                    consecutive_hits += 1
                    
                    # Determine signal strength level
                    if rssi > -50:
                        strength = "🟢 Strong"
                    elif rssi > -70:
                        strength = "🟡 Medium"
                    else:
                        strength = "🔴 Weak"
                    
                    print(f"📶 {rssi:3} dBm {strength}")
                    
                    # Check if device came back in range
                    if not self.device_in_range and consecutive_hits >= 2:
                        self.device_in_range = True
                        print("🔓 Device back in range!")
                        self._execute_system_action('wake')
                
                else:
                    # Device not detected
                    consecutive_hits = 0
                    consecutive_misses += 1
                    print(f"❌ Not detected ({consecutive_misses})")
                    
                    # Check if device went out of range
                    required_misses = max(2, settings.MIN_OUT_OF_RANGE_TIME // settings.SCAN_INTERVAL)
                    if self.device_in_range and consecutive_misses >= required_misses:
                        self.device_in_range = False
                        print("🔒 DEVICE OUT OF RANGE - LOCKING")
                        self._execute_system_action('lock')
                
                # Show performance stats periodically
                if self.performance_stats['scans_performed'] % 20 == 0:
                    stats = self.get_performance_stats()
                    print(f"📈 Stats: {stats['success_rate']:.1f}% success | {stats['runtime_minutes']:.1f}min runtime")
                
                await asyncio.sleep(settings.SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n⏹️ Monitoring stopped by user")
            stats = self.get_performance_stats()
            print(f"📊 Final Stats: {stats['scans_performed']} scans, {stats['success_rate']:.1f}% success")

async def main():
    """Main application entry point"""
    bluelock = EnhancedBlueLock()
    
    print("🔒 BlueLock - Enhanced Bluetooth Proximity Monitor")
    print("=" * 60)
    
    # Check if device is already configured
    if bluelock.target_device:
        print(f"✅ Using configured device: {bluelock.target_device['name']}")
        print(f"   Address: {bluelock.target_device['address']}")
        
        # Confirm to continue
        choice = input("\nContinue with this device? (y/n): ").strip().lower()
        if choice == 'y':
            await bluelock.monitor_device()
            return
    
    # Device selection
    print("🔍 Discovering devices...")
    devices = bluelock.get_enhanced_device_list()
    
    if not devices:
        print("❌ No devices found!")
        print("💡 Make sure your Bluetooth devices are:")
        print("   • Paired with Windows")
        print("   • Turned ON")
        print("   • Close to your computer")
        return
    
    # Display devices
    print(f"\n📋 Found {len(devices)} device(s):")
    print("─" * 60)
    for i, device in enumerate(devices, 1):
        print(f" {i:2d}. {device['name']:<25} {device['address']}")
    print("─" * 60)
    
    # Device selection
    while True:
        try:
            choice = input(f"Select device (1-{len(devices)}): ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(devices):
                selected = devices[idx]
                bluelock.target_device = {
                    'address': selected['address'],
                    'name': selected['name']
                }
                bluelock.paired_devices[selected['address']] = {
                    'name': selected['name'],
                    'configured_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'Connected'
                }
                bluelock._save_config()
                
                print(f"✅ Configured: {selected['name']}")
                break
            else:
                print("❌ Invalid selection!")
                
        except ValueError:
            print("❌ Please enter a number!")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            return
    
    # Start monitoring
    await bluelock.monitor_device()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")