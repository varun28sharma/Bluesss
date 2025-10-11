"""
Bluetooth Diagnostic Tool for BlueLock
Helps identify connection issues
"""

import asyncio
import subprocess
import re
from bleak import BleakScanner

async def diagnose_bluetooth():
    print("🔍 BlueLock Bluetooth Diagnostic Tool")
    print("=" * 50)
    
    # 1. Check system paired devices
    print("\n📱 STEP 1: Checking Windows paired devices...")
    try:
        cmd = 'Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq "OK" -and $_.FriendlyName -like "*Redmi*" -or $_.FriendlyName -like "*Galaxy*"} | Select-Object FriendlyName, InstanceId'
        result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            print("✅ Found paired phone devices:")
            lines = result.stdout.strip().split('\n')
            for line in lines[2:]:  # Skip headers
                if line.strip() and 'DEV_' in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ No phone devices found in Windows pairing")
    except Exception as e:
        print(f"❌ Error checking paired devices: {e}")
    
    # 2. Check Bluetooth LE scanning
    print("\\n📡 STEP 2: Testing Bluetooth LE scanning...")
    devices_found = []
    
    def detection_callback(device, advertisement_data):
        devices_found.append({
            'name': device.name or 'Unknown',
            'address': device.address,
            'rssi': advertisement_data.rssi
        })
        print(f"   📶 Found: {device.name or 'Unknown'} ({device.address}) - {advertisement_data.rssi} dBm")
    
    try:
        scanner = BleakScanner(detection_callback)
        print("   Scanning for 10 seconds...")
        await scanner.start()
        await asyncio.sleep(10)
        await scanner.stop()
        
        if devices_found:
            print(f"\n✅ BLE scan found {len(devices_found)} devices")
            # Check if any match paired devices
            print("\n📋 Strongest signals:")
            sorted_devices = sorted(devices_found, key=lambda x: x['rssi'], reverse=True)
            for device in sorted_devices[:5]:
                signal = "🟢 Strong" if device['rssi'] > -60 else "🟡 Medium" if device['rssi'] > -80 else "🔴 Weak"
                print(f"   {device['name'][:20]:<20} {device['address']} {device['rssi']:3} dBm {signal}")
        else:
            print("❌ No BLE devices detected - this might be the issue!")
            
    except Exception as e:
        print(f"❌ BLE scanning failed: {e}")
    
    # 3. Check specific target device
    print("\n🎯 STEP 3: Testing connection to your configured device...")
    try:
        import json
        if os.path.exists('paired_devices.json'):
            with open('paired_devices.json', 'r') as f:
                config = json.load(f)
            
            for address, info in config.items():
                print(f"   Testing: {info['name']} ({address})")
                
                # Try direct scan for this device
                found_rssi = None
                def target_callback(device, advertisement_data):
                    nonlocal found_rssi
                    if device.address.lower() == address.lower():
                        found_rssi = advertisement_data.rssi
                
                scanner = BleakScanner(target_callback)
                await scanner.start()
                await asyncio.sleep(5)
                await scanner.stop()
                
                if found_rssi:
                    print(f"   ✅ Device detected with {found_rssi} dBm signal")
                else:
                    print(f"   ❌ Device not detected - possible issues:")
                    print(f"      • Device Bluetooth is OFF")
                    print(f"      • Device is too far away")
                    print(f"      • Device is in sleep mode")
                    print(f"      • Bluetooth LE is disabled on device")
        else:
            print("   No configured devices found")
            
    except Exception as e:
        print(f"❌ Error testing configured device: {e}")
    
    # 4. Recommendations
    print("\n💡 TROUBLESHOOTING RECOMMENDATIONS:")
    print("=" * 50)
    print("1. 📱 On your phone/device:")
    print("   • Make sure Bluetooth is ON")
    print("   • Enable 'Bluetooth LE' or 'BLE' if available") 
    print("   • Keep device awake/active during testing")
    print("   • Move device closer (within 10 feet)")
    
    print("\n2. 💻 On your laptop:")
    print("   • Make sure Bluetooth is ON in Windows Settings")
    print("   • Try: Settings > Devices > Bluetooth & other devices")
    print("   • Restart Bluetooth service if needed")
    
    print("\n3. 🔧 Technical checks:")
    print("   • Check if device supports Bluetooth LE advertising")
    print("   • Some devices only advertise when not connected to anything")
    print("   • Try unpairing and re-pairing the device")
    
    print("\n4. 🎯 For BlueLock specifically:")
    print("   • Some paired devices don't broadcast BLE advertisements")
    print("   • Try using headphones/earbuds instead of phones")
    print("   • AirPods, Galaxy Buds work better than phones sometimes")

if __name__ == "__main__":
    import os
    asyncio.run(diagnose_bluetooth())