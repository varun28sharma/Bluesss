"""
BlueLock Desktop App - Modern GUI with System Tray
Professional desktop application for Bluetooth proximity monitoring
"""

import asyncio
import customtkinter as ctk
import threading
import time
import json
import os
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import sys
from plyer import notification
import logging

# Import our optimized BlueLock core
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'archive'))
from bluelock_fixed import EnhancedBlueLock
import settings

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class BlueLockGUI:
    def __init__(self):
        # Main window
        self.root = ctk.CTk()
        self.root.title("BlueLock - Proximity Monitor")
        self.root.geometry("600x500")
        self.root.iconbitmap() if hasattr(self.root, 'iconbitmap') else None
        
        # Core BlueLock instance
        self.bluelock = EnhancedBlueLock()
        self.monitoring_task = None
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # System tray
        self.tray_icon = None
        
        # UI State
        self.device_list = []
        self.selected_device = None
        
        # Setup UI
        self.setup_ui()
        self.setup_system_tray()
        
        # Load saved device if exists
        self.load_saved_device()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Create the main GUI interface"""
        
        # Header
        header_frame = ctk.CTkFrame(self.root, height=80)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="🔐 BlueLock", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=20)
        
        subtitle_label = ctk.CTkLabel(
            header_frame, 
            text="Bluetooth Proximity Monitor", 
            font=ctk.CTkFont(size=14),
            text_color="gray70"
        )
        subtitle_label.pack(side="left", padx=(0, 20), pady=20)
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(header_frame, width=120, height=40)
        self.status_frame.pack(side="right", padx=20, pady=20)
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="● Stopped", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="red"
        )
        self.status_label.pack(expand=True)
        
        # Main content area
        content_frame = ctk.CTkFrame(self.root)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Device selection section
        device_section = ctk.CTkFrame(content_frame)
        device_section.pack(fill="x", padx=20, pady=20)
        
        device_title = ctk.CTkLabel(
            device_section, 
            text="📱 Device Selection", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        device_title.pack(padx=20, pady=(20, 10))
        
        # Device info display
        self.device_info_frame = ctk.CTkFrame(device_section)
        self.device_info_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.device_info_label = ctk.CTkLabel(
            self.device_info_frame,
            text="No device configured",
            font=ctk.CTkFont(size=14),
            text_color="gray70"
        )
        self.device_info_label.pack(pady=15)
        
        # Buttons
        button_frame = ctk.CTkFrame(device_section)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.scan_button = ctk.CTkButton(
            button_frame,
            text="🔍 Scan for Devices",
            command=self.scan_devices,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.scan_button.pack(side="left", padx=(20, 10), pady=15)
        
        self.select_button = ctk.CTkButton(
            button_frame,
            text="📱 Select Device",
            command=self.show_device_selection,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.select_button.pack(side="left", padx=10, pady=15)
        
        # Monitoring section
        monitor_section = ctk.CTkFrame(content_frame)
        monitor_section.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        monitor_title = ctk.CTkLabel(
            monitor_section, 
            text="🎯 Monitoring", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        monitor_title.pack(padx=20, pady=(20, 10))
        
        # Status display
        self.status_text = ctk.CTkTextbox(
            monitor_section, 
            height=150,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.status_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.status_text.insert("0.0", "Ready to start monitoring...\n")
        
        # Control buttons
        control_frame = ctk.CTkFrame(monitor_section)
        control_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.start_button = ctk.CTkButton(
            control_frame,
            text="▶️ Start Monitoring",
            command=self.start_monitoring,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.start_button.pack(side="left", padx=(20, 10), pady=15, fill="x", expand=True)
        
        self.stop_button = ctk.CTkButton(
            control_frame,
            text="⏹️ Stop Monitoring",
            command=self.stop_monitoring,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=10, pady=15, fill="x", expand=True)
        
        self.minimize_button = ctk.CTkButton(
            control_frame,
            text="📊 Minimize to Tray",
            command=self.minimize_to_tray,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="orange",
            hover_color="darkorange"
        )
        self.minimize_button.pack(side="right", padx=(10, 20), pady=15)
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        # Create tray icon
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        draw.text((24, 24), "🔐", fill='blue')
        
        menu = pystray.Menu(
            item('Show BlueLock', self.show_window, default=True),
            item('Start Monitoring', self.start_monitoring_tray, enabled=lambda _: not self.is_monitoring),
            item('Stop Monitoring', self.stop_monitoring_tray, enabled=lambda _: self.is_monitoring),
            pystray.Menu.SEPARATOR,
            item('Settings', self.show_settings),
            item('Exit', self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("BlueLock", image, "BlueLock - Proximity Monitor", menu)
    
    def load_saved_device(self):
        """Load previously configured device"""
        if self.bluelock.paired_devices:
            first_addr = list(self.bluelock.paired_devices.keys())[0]
            device_info = self.bluelock.paired_devices[first_addr]
            self.selected_device = {
                'address': first_addr,
                'name': device_info['name']
            }
            self.update_device_display()
    
    def update_device_display(self):
        """Update device information display"""
        if self.selected_device:
            device_text = f"🔗 {self.selected_device['name']}\n📍 {self.selected_device['address']}"
            self.device_info_label.configure(text=device_text, text_color="lightgreen")
            self.start_button.configure(state="normal")
        else:
            self.device_info_label.configure(text="No device configured", text_color="gray70")
            self.start_button.configure(state="disabled")
    
    def scan_devices(self):
        """Scan for available devices"""
        self.log_status("🔍 Scanning for devices...")
        self.scan_button.configure(state="disabled", text="Scanning...")
        
        # Run scan in thread to avoid blocking UI
        threading.Thread(target=self._scan_devices_thread, daemon=True).start()
    
    def _scan_devices_thread(self):
        """Background device scanning"""
        try:
            # Get connected devices
            devices = self.bluelock.get_enhanced_device_list()
            self.device_list = devices
            
            # Update UI on main thread
            self.root.after(0, self._scan_complete, devices)
        except Exception as e:
            self.root.after(0, self._scan_error, str(e))
    
    def _scan_complete(self, devices):
        """Handle scan completion"""
        self.scan_button.configure(state="normal", text="🔍 Scan for Devices")
        
        if devices:
            self.log_status(f"✅ Found {len(devices)} device(s)")
            self.select_button.configure(state="normal")
        else:
            self.log_status("❌ No devices found")
            self.select_button.configure(state="disabled")
    
    def _scan_error(self, error):
        """Handle scan error"""
        self.scan_button.configure(state="normal", text="🔍 Scan for Devices")
        self.log_status(f"❌ Scan failed: {error}")
    
    def show_device_selection(self):
        """Show device selection dialog"""
        if not self.device_list:
            return
        
        # Create device selection window
        selection_window = ctk.CTkToplevel(self.root)
        selection_window.title("Select Device")
        selection_window.geometry("500x400")
        selection_window.transient(self.root)
        selection_window.grab_set()
        
        # Title
        title_label = ctk.CTkLabel(
            selection_window,
            text="📱 Select Device to Monitor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Device list
        list_frame = ctk.CTkScrollableFrame(
            selection_window,
            label_text="Available Devices"
        )
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        selected_var = ctk.StringVar()
        
        for i, device in enumerate(self.device_list):
            device_frame = ctk.CTkFrame(list_frame)
            device_frame.pack(fill="x", padx=10, pady=5)
            
            radio = ctk.CTkRadioButton(
                device_frame,
                text=f"{device['name']} ({device['address']})",
                variable=selected_var,
                value=str(i),
                font=ctk.CTkFont(size=14)
            )
            radio.pack(anchor="w", padx=15, pady=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(selection_window)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        def confirm_selection():
            try:
                selected_idx = int(selected_var.get())
                selected_device = self.device_list[selected_idx]
                
                # Configure BlueLock
                device_info = {
                    'name': selected_device['name'],
                    'configured_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'Connected'
                }
                
                self.bluelock.paired_devices[selected_device['address']] = device_info
                self.bluelock.target_device = {
                    'address': selected_device['address'],
                    'name': selected_device['name']
                }
                self.bluelock._save_config()
                
                self.selected_device = self.bluelock.target_device
                self.update_device_display()
                self.log_status(f"✅ Configured device: {selected_device['name']}")
                
                selection_window.destroy()
            except (ValueError, IndexError):
                pass
        
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="✅ Confirm Selection",
            command=confirm_selection,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        confirm_btn.pack(side="right", padx=(10, 20), pady=15)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=selection_window.destroy,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="right", padx=20, pady=15)
    
    def start_monitoring(self):
        """Start proximity monitoring"""
        if not self.selected_device:
            self.log_status("❌ Please select a device first")
            return
        
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.log_status(f"🎯 Starting monitoring: {self.selected_device['name']}")
        
        # Update UI
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="● Monitoring", text_color="green")
        
        # Start monitoring in separate thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Show notification
        self.show_notification("BlueLock Started", f"Monitoring {self.selected_device['name']}")
    
    def stop_monitoring(self):
        """Stop proximity monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.log_status("⏹️ Stopping monitoring...")
        
        # Update UI
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text="● Stopped", text_color="red")
        
        # Show notification
        self.show_notification("BlueLock Stopped", "Proximity monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        consecutive_misses = 0
        consecutive_hits = 0
        
        while self.is_monitoring:
            try:
                # Run async scan in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                rssi = loop.run_until_complete(
                    self.bluelock._optimized_scan(self.selected_device['address'])
                )
                
                loop.close()
                
                if rssi is not None:
                    # Device detected
                    consecutive_misses = 0
                    consecutive_hits += 1
                    
                    signal_strength = (
                        "🟢 Strong" if rssi > -50 else 
                        "🟡 Medium" if rssi > -70 else 
                        "🔴 Weak"
                    )
                    
                    status_msg = f"📶 {rssi:3} dBm {signal_strength}"
                    self.root.after(0, self.log_status, status_msg)
                    
                    # Wake if device was out of range
                    if not self.bluelock.device_in_range and consecutive_hits >= 2:
                        self.bluelock.device_in_range = True
                        wake_msg = "🔓 Device back in range!"
                        self.root.after(0, self.log_status, wake_msg)
                        self.root.after(0, self.show_notification, "Device Detected", "Device back in range")
                        
                        if settings.ENABLE_WAKE:
                            self.bluelock._execute_system_action('wake')
                
                else:
                    # Device not detected
                    consecutive_hits = 0
                    consecutive_misses += 1
                    
                    status_msg = f"❌ Not detected ({consecutive_misses})"
                    self.root.after(0, self.log_status, status_msg)
                    
                    # Lock after threshold
                    required_misses = settings.MIN_OUT_OF_RANGE_TIME // settings.SCAN_INTERVAL
                    if (self.bluelock.device_in_range and consecutive_misses >= required_misses):
                        self.bluelock.device_in_range = False
                        lock_msg = "🔒 DEVICE OUT OF RANGE - LOCKING"
                        self.root.after(0, self.log_status, lock_msg)
                        self.root.after(0, self.show_notification, "Device Lost", "Computer locked for security")
                        
                        if settings.ENABLE_LOCK:
                            self.bluelock._execute_system_action('lock')
                
                time.sleep(settings.SCAN_INTERVAL)
                
            except Exception as e:
                error_msg = f"⚠️ Monitor error: {str(e)}"
                self.root.after(0, self.log_status, error_msg)
                time.sleep(settings.SCAN_INTERVAL)
    
    def log_status(self, message):
        """Add message to status log"""
        timestamp = time.strftime("[%H:%M:%S]")
        full_message = f"{timestamp} {message}\n"
        
        self.status_text.insert("end", full_message)
        self.status_text.see("end")
        
        # Limit log size
        content = self.status_text.get("0.0", "end")
        lines = content.split("\n")
        if len(lines) > 100:
            # Keep last 80 lines
            new_content = "\n".join(lines[-80:])
            self.status_text.delete("0.0", "end")
            self.status_text.insert("0.0", new_content)
    
    def show_notification(self, title, message):
        """Show system notification"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_icon=None,
                timeout=3
            )
        except:
            pass  # Notifications not supported
    
    def minimize_to_tray(self):
        """Minimize to system tray"""
        self.root.withdraw()
        if not self.tray_icon._running:
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def show_window(self, icon=None, item=None):
        """Show main window from tray"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def start_monitoring_tray(self, icon, item):
        """Start monitoring from tray"""
        self.start_monitoring()
    
    def stop_monitoring_tray(self, icon, item):
        """Stop monitoring from tray"""
        self.stop_monitoring()
    
    def show_settings(self, icon=None, item=None):
        """Show settings window"""
        # Create settings window
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("BlueLock Settings")
        settings_window.geometry("400x500")
        if not self.root.winfo_viewable():
            self.show_window()
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Settings content
        title_label = ctk.CTkLabel(
            settings_window,
            text="⚙️ BlueLock Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Settings frame
        settings_frame = ctk.CTkScrollableFrame(settings_window)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # RSSI Threshold
        rssi_label = ctk.CTkLabel(settings_frame, text="RSSI Threshold (dBm):", font=ctk.CTkFont(size=14, weight="bold"))
        rssi_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        rssi_var = ctk.StringVar(value=str(settings.RSSI_THRESHOLD))
        rssi_entry = ctk.CTkEntry(settings_frame, textvariable=rssi_var, width=200)
        rssi_entry.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Scan Interval
        interval_label = ctk.CTkLabel(settings_frame, text="Scan Interval (seconds):", font=ctk.CTkFont(size=14, weight="bold"))
        interval_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        interval_var = ctk.StringVar(value=str(settings.SCAN_INTERVAL))
        interval_entry = ctk.CTkEntry(settings_frame, textvariable=interval_var, width=200)
        interval_entry.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Enable Lock
        lock_var = ctk.BooleanVar(value=settings.ENABLE_LOCK)
        lock_checkbox = ctk.CTkCheckBox(settings_frame, text="Enable Auto-Lock", variable=lock_var, font=ctk.CTkFont(size=14))
        lock_checkbox.pack(anchor="w", padx=20, pady=10)
        
        # Enable Wake
        wake_var = ctk.BooleanVar(value=settings.ENABLE_WAKE)
        wake_checkbox = ctk.CTkCheckBox(settings_frame, text="Enable Auto-Wake", variable=wake_var, font=ctk.CTkFont(size=14))
        wake_checkbox.pack(anchor="w", padx=20, pady=10)
        
        def save_settings():
            try:
                # Update settings module
                settings.RSSI_THRESHOLD = int(rssi_var.get())
                settings.SCAN_INTERVAL = float(interval_var.get())
                settings.ENABLE_LOCK = lock_var.get()
                settings.ENABLE_WAKE = wake_var.get()
                
                # Save to file (optional - you could implement settings persistence)
                self.log_status("✅ Settings saved")
                settings_window.destroy()
            except ValueError as e:
                self.log_status(f"❌ Invalid settings: {e}")
        
        # Buttons
        button_frame = ctk.CTkFrame(settings_window)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        save_btn = ctk.CTkButton(button_frame, text="💾 Save", command=save_settings, height=40)
        save_btn.pack(side="right", padx=(10, 20), pady=15)
        
        cancel_btn = ctk.CTkButton(button_frame, text="❌ Cancel", command=settings_window.destroy, height=40, fg_color="gray")
        cancel_btn.pack(side="right", padx=20, pady=15)
    
    def on_closing(self):
        """Handle window close event"""
        if self.is_monitoring:
            # Minimize to tray instead of closing
            self.minimize_to_tray()
        else:
            self.quit_app()
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        self.is_monitoring = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        sys.exit()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main application entry point"""
    try:
        app = BlueLockGUI()
        app.run()
    except KeyboardInterrupt:
        print("\\nApplication stopped by user")
    except Exception as e:
        print(f"Application error: {e}")
        logging.error(f"Application error: {e}")

if __name__ == "__main__":
    main()