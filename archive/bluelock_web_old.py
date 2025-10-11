"""
BlueLock Web Interface
Simple web-based control panel for BlueLock
"""

from flask import Flask, render_template, jsonify, request
import threading
import asyncio
import json
import time
from bluelock_fixed import EnhancedBlueLock
import settings

app = Flask(__name__)
bluelock_instance = EnhancedBlueLock()
monitoring_active = False
monitoring_thread = None
status_log = []

@app.route('/')
def index():
    """Main web interface"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current status"""
    return jsonify({
        'monitoring': monitoring_active,
        'device': bluelock_instance.target_device,
        'paired_devices': bluelock_instance.paired_devices,
        'log': status_log[-20:]  # Last 20 entries
    })

@app.route('/api/devices')
def get_devices():
    """Get available devices"""
    try:
        devices = bluelock_instance.get_enhanced_device_list()
        return jsonify({'success': True, 'devices': devices})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/configure', methods=['POST'])
def configure_device():
    """Configure target device"""
    try:
        data = request.json
        address = data['address']
        name = data['name']
        
        # Configure device
        device_info = {
            'name': name,
            'configured_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Connected'
        }
        
        bluelock_instance.paired_devices[address] = device_info
        bluelock_instance.target_device = {'address': address, 'name': name}
        bluelock_instance._save_config()
        
        add_log(f"✅ Configured device: {name}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start monitoring"""
    global monitoring_active, monitoring_thread
    
    if not bluelock_instance.target_device:
        return jsonify({'success': False, 'error': 'No device configured'})
    
    if monitoring_active:
        return jsonify({'success': False, 'error': 'Already monitoring'})
    
    monitoring_active = True
    monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitoring_thread.start()
    
    add_log(f"🎯 Started monitoring: {bluelock_instance.target_device['name']}")
    return jsonify({'success': True})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring"""
    global monitoring_active
    monitoring_active = False
    add_log("⏹️ Stopped monitoring")
    return jsonify({'success': True})

def add_log(message):
    """Add message to status log"""
    timestamp = time.strftime('[%H:%M:%S]')
    status_log.append(f"{timestamp} {message}")
    
    # Keep only last 100 entries
    if len(status_log) > 100:
        status_log[:] = status_log[-100:]

def monitoring_loop():
    """Background monitoring loop"""
    consecutive_misses = 0
    consecutive_hits = 0
    
    while monitoring_active:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            rssi = loop.run_until_complete(
                bluelock_instance.enhanced_scan_for_device(bluelock_instance.target_device['address'])
            )
            loop.close()
            
            if rssi is not None:
                consecutive_misses = 0
                consecutive_hits += 1
                
                signal_strength = (
                    "🟢 Strong" if rssi > -50 else 
                    "🟡 Medium" if rssi > -70 else 
                    "🔴 Weak"
                )
                
                add_log(f"📶 {rssi:3} dBm {signal_strength}")
                
                if not bluelock_instance.device_in_range and consecutive_hits >= 2:
                    bluelock_instance.device_in_range = True
                    add_log("🔓 Device back in range!")
                    if settings.ENABLE_WAKE:
                        bluelock_instance._execute_system_action('wake')
            else:
                consecutive_hits = 0
                consecutive_misses += 1
                add_log(f"❌ Not detected ({consecutive_misses})")
                
                required_misses = settings.MIN_OUT_OF_RANGE_TIME // settings.SCAN_INTERVAL
                if (bluelock_instance.device_in_range and consecutive_misses >= required_misses):
                    bluelock_instance.device_in_range = False
                    add_log("🔒 DEVICE OUT OF RANGE - LOCKING")
                    if settings.ENABLE_LOCK:
                        bluelock_instance._execute_system_action('lock')
            
            time.sleep(settings.SCAN_INTERVAL)
            
        except Exception as e:
            add_log(f"⚠️ Error: {str(e)}")
            time.sleep(settings.SCAN_INTERVAL)

if __name__ == '__main__':
    print("🌐 Starting BlueLock Web Interface...")
    print("📱 Open http://localhost:5000 in your browser")
    app.run(host='0.0.0.0', port=5000, debug=False)