"""
Enhanced BlueLock Scanner - Improved Device Detection
Fixes connectivity issues with multiple scanning approaches
"""

import asyncio
import time
import subprocess
import re
from bleak import BleakScanner, BleakClient
import json
import logging

class EnhancedBlueLockScanner:
    def __init__(self):
        self.found_devices = {}
        self.paired_devices = {}
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)

    def get_windows_paired_devices(self):
        """Get paired devices from Windows registry/PowerShell"""
        try:
            # Method 1: PowerShell command to get paired devices
            cmd = '''Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq "OK"} | Select-Object FriendlyName, InstanceId'''
            result = subprocess.run(['powershell', '-Command', cmd], 
                                  capture_output=True, text=True, timeout=10)
            
            devices = {}
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[3:]  # Skip headers
                for line in lines:
                    if line.strip() and not line.startswith('-'):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            name = ' '.join(parts[:-1])
                            instance_id = parts[-1]
                            
                            # Extract MAC address from instance ID
                            mac_match = re.search(r'DEV_([A-F0-9]{12})', instance_id)
                            if mac_match:
                                mac_hex = mac_match.group(1)
                                mac = ':'.join([mac_hex[i:i+2] for i in range(0, 12, 2)])
                                devices[mac] = {
                                    'name': name,
                                    'status': 'Paired',
                                    'method': 'Windows Registry'
                                }
            
            self.logger.info(f"Found {len(devices)} paired devices via PowerShell")
            return devices
            
        except Exception as e:
            self.logger.error(f"Error getting Windows paired devices: {e}")
            return {}

    async def enhanced_ble_scan(self, duration=15):
        """Enhanced BLE scan with multiple detection methods"""
        print(f"🔍 Starting enhanced BLE scan for {duration} seconds...")
        
        found_devices = {}
        
        def detection_callback(device, advertisement_data):
            if device.address not in found_devices:
                found_devices[device.address] = {
                    'name': device.name or 'Unknown',
                    'address': device.address,
                    'rssi': advertisement_data.rssi,
                    'method': 'BLE Advertisement'
                }
                print(f"   📶 Detected: {device.name or 'Unknown'} ({device.address}) - {advertisement_data.rssi} dBm")

        try:
            # Start scanning
            scanner = BleakScanner(detection_callback)
            await scanner.start()
            await asyncio.sleep(duration)
            await scanner.stop()
            
        except Exception as e:
            self.logger.error(f"BLE scan error: {e}")
        
        print(f"✅ BLE scan completed - found {len(found_devices)} devices")
        return found_devices

    async def try_direct_connection(self, address):
        """Try to directly connect to a device to test if it's available"""
        try:
            print(f"🔌 Testing direct connection to {address}...")
            async with BleakClient(address, timeout=5.0) as client:
                if client.is_connected:
                    print(f"✅ Successfully connected to {address}")
                    return True
        except Exception as e:
            print(f"❌ Connection failed to {address}: {e}")
            return False

    async def comprehensive_device_scan(self):
        """Comprehensive scan using multiple methods"""
        print("🚀 Starting comprehensive device discovery...")
        print("=" * 60)
        
        all_devices = {}
        
        # Method 1: Get Windows paired devices
        print("\n📱 STEP 1: Getting Windows paired devices...")
        paired_devices = self.get_windows_paired_devices()
        for mac, info in paired_devices.items():
            all_devices[mac] = info
            print(f"   ✅ {info['name']:<25} {mac}")
        
        # Method 2: BLE Advertisement scan
        print(f"\n📡 STEP 2: BLE Advertisement scan...")
        ble_devices = await self.enhanced_ble_scan(10)
        for mac, info in ble_devices.items():
            if mac in all_devices:
                all_devices[mac]['rssi'] = info['rssi']
                all_devices[mac]['active'] = True
                print(f"   🔄 Updated: {info['name']:<25} {mac} - {info['rssi']} dBm")
            else:
                all_devices[mac] = info
                all_devices[mac]['active'] = True
        
        # Method 3: Test direct connections to paired devices
        print(f"\n🔌 STEP 3: Testing direct connections...")
        connection_tasks = []
        for mac, info in paired_devices.items():
            if 'active' not in info:  # Only test devices not found in BLE scan
                connection_tasks.append(self.try_direct_connection(mac))
        
        if connection_tasks:
            results = await asyncio.gather(*connection_tasks, return_exceptions=True)
            for i, (mac, info) in enumerate(paired_devices.items()):
                if 'active' not in info and i < len(results):
                    if results[i] is True:
                        all_devices[mac]['connectable'] = True
                        print(f"   ✅ Connectable: {info['name']}")
        
        return all_devices

    async def smart_device_selection(self):
        """Smart device selection with enhanced detection"""
        devices = await self.comprehensive_device_scan()
        
        print(f"\n📋 DEVICE SUMMARY:")
        print("=" * 60)
        
        if not devices:
            print("❌ No devices found!")
            return None
        
        # Categorize devices
        active_devices = {k: v for k, v in devices.items() if v.get('active', False)}
        paired_devices = {k: v for k, v in devices.items() if v.get('status') == 'Paired'}
        connectable_devices = {k: v for k, v in devices.items() if v.get('connectable', False)}
        
        print(f"📊 Statistics:")
        print(f"   Total devices found: {len(devices)}")
        print(f"   Active (broadcasting): {len(active_devices)}")
        print(f"   Paired in Windows: {len(paired_devices)}")
        print(f"   Directly connectable: {len(connectable_devices)}")
        
        # Show devices by category
        categories = [
            ("🟢 ACTIVE DEVICES (Broadcasting BLE)", active_devices),
            ("🔵 PAIRED DEVICES (Windows)", paired_devices),
            ("🟡 CONNECTABLE DEVICES", connectable_devices),
            ("⚪ ALL OTHER DEVICES", {k: v for k, v in devices.items() 
                                   if k not in active_devices and k not in paired_devices and k not in connectable_devices})
        ]
        
        device_list = []
        for category_name, category_devices in categories:
            if category_devices:
                print(f"\n{category_name}:")
                print("-" * 50)
                for mac, info in category_devices.items():
                    device_list.append((mac, info))
                    rssi_info = f" - {info['rssi']} dBm" if 'rssi' in info else ""
                    status_info = f" [{info.get('method', 'Unknown')}]"
                    print(f" {len(device_list):2d}. {info['name']:<25} {mac}{rssi_info}{status_info}")
        
        if not device_list:
            print("❌ No suitable devices found for BlueLock!")
            return None
        
        # Device selection
        print(f"\n🎯 SELECT DEVICE FOR BLUELOCK:")
        print("-" * 50)
        while True:
            try:
                choice = input(f"Select device (1-{len(device_list)}) or 'r' to rescan: ").strip().lower()
                
                if choice == 'r':
                    print("\n🔄 Rescanning...")
                    return await self.smart_device_selection()
                
                idx = int(choice) - 1
                if 0 <= idx < len(device_list):
                    selected_mac, selected_info = device_list[idx]
                    print(f"\n✅ Selected: {selected_info['name']} ({selected_mac})")
                    
                    # Save configuration
                    config = {
                        'target_device': {'address': selected_mac, 'name': selected_info['name']},
                        'configured_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'device_info': selected_info
                    }
                    
                    with open('enhanced_bluelock_config.json', 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    return selected_mac, selected_info
                else:
                    print("❌ Invalid selection!")
                    
            except ValueError:
                print("❌ Please enter a number!")
            except KeyboardInterrupt:
                print("\n❌ Cancelled by user")
                return None

async def main():
    """Main function to run enhanced device discovery"""
    scanner = EnhancedBlueLockScanner()
    
    print("🔒 BlueLock Enhanced Device Scanner")
    print("=" * 60)
    print("This tool will help you find and configure devices for BlueLock")
    print("with improved detection methods.\n")
    
    result = await scanner.smart_device_selection()
    
    if result:
        mac, info = result
        print(f"\n🎉 SUCCESS!")
        print(f"Device configured: {info['name']} ({mac})")
        print(f"Configuration saved to: enhanced_bluelock_config.json")
        print(f"\nYou can now use this device with BlueLock!")
    else:
        print(f"\n❌ No device configured.")
        print(f"Please ensure your Bluetooth devices are:")
        print(f"  • Turned ON")
        print(f"  • Paired with Windows") 
        print(f"  • Close to your computer (within 10 feet)")
        print(f"  • Not in sleep/power save mode")

if __name__ == "__main__":
    asyncio.run(main())