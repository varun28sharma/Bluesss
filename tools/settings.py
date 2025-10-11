# ===== BlueLock Optimized Configuration =====

# Device Storage
PAIRED_DEVICES_FILE = "paired_devices.json"

# Performance Settings (Optimized)
RSSI_THRESHOLD = -70        # Signal strength threshold (-50=close, -70=medium, -90=far)
SCAN_INTERVAL = 2.5         # Seconds between scans (optimized for balance of speed/battery)
DISCOVERY_TIMEOUT = 8       # Device discovery timeout (shorter for faster startup)

# System Actions
ENABLE_LOCK = True          # Lock computer when out of range
ENABLE_WAKE = True          # Wake/unlock when back in range

# Timing Configuration (Optimized)
MIN_OUT_OF_RANGE_TIME = 6   # Seconds before locking (2-3 missed scans)
MIN_IN_RANGE_TIME = 3       # Seconds before wake action

# Advanced Performance
MAX_SCAN_FAILURES = 50      # Reset scanner after failures
LOG_LEVEL = "INFO"          # Logging level (DEBUG, INFO, WARNING, ERROR)
ENABLE_STATS = True         # Show performance statistics