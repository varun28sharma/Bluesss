# 🔵 BlueLock Simple

**Auto screen control based on Bluetooth device proximity**

Turn off your screen automatically when your Bluetooth device (headphones, earbuds, etc.) disconnects or goes out of range.

## ✨ Features

- 🔍 **Auto-detection** - Automatically finds your connected Bluetooth device
- 📴 **Screen OFF** - Turns off screen when device disconnects
- 🔵 **Screen ON** - Screen stays on while device is connected
- ⚡ **No setup needed** - Just run and go

## 📋 Requirements

- Windows 10/11
- Python 3.8+
- Bluetooth device (headphones, earbuds, phone, etc.)

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Connect your Bluetooth device** (headphones, earbuds, etc.)

3. **Run the script:**
   ```bash
   python main/bluelock_simple.py
   ```

## 📱 How It Works

1. Script auto-detects your connected Bluetooth device
2. Monitors the connection status every 3 seconds
3. When device disconnects → Screen turns OFF
4. Move mouse or press any key → Screen wakes up
5. When device reconnects → Monitoring resumes

## ⚙️ Settings

Edit `main/bluelock_simple.py` to adjust:

```python
CHECK_INTERVAL = 3.0      # Check every 3 seconds
OUT_OF_RANGE_COUNT = 2    # Wait 2 checks before turning off (~6 sec)
```

## 📁 Project Structure

```
Bluesss/
├── main/
│   └── bluelock_simple.py   # Main script
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## 🛑 To Stop

Press `Ctrl+C` in the terminal to stop monitoring.

## 📝 License

MIT License
