# 🔵 BlueLock

**Bluetooth Screen Control - Turn off your screen when your Bluetooth device disconnects**

[![Build](https://github.com/varun28sharma/Bluesss/actions/workflows/build.yml/badge.svg)](https://github.com/varun28sharma/Bluesss/actions/workflows/build.yml)

## ✨ Features

- 🔍 **Auto-detection** - Automatically finds connected Bluetooth audio devices
- 📴 **Screen OFF** - Turns off screen when device disconnects
- 🌐 **Web Interface** - Control from any device on your network
- 📱 **Mobile Friendly** - Access from phone or tablet
- ⚡ **No setup needed** - Just run and go

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the web server:**
   ```bash
   python app.py
   ```

3. **Open in browser:**
   - Local: http://127.0.0.1:5000
   - Network: http://YOUR_IP:5000 (access from phone/tablet)

### Option 2: Command Line

```bash
python main/bluelock_simple.py
```

Or double-click `run.bat`

## 📱 Web Interface

Access BlueLock from any device on your network:

1. Run `python app.py` on your Windows PC
2. Open the URL shown in terminal on any device
3. Select your Bluetooth device
4. Click "Start Monitoring"

**Features:**
- View all Bluetooth devices
- Start/Stop monitoring
- See connection status in real-time
- Manual screen off button

## 📋 Requirements

- Windows 10/11
- Python 3.8+
- Bluetooth audio device (headphones, earbuds, etc.)

## 📁 Project Structure

```
Bluesss/
├── app.py                 # Flask web server
├── main/
│   └── bluelock_simple.py # Command line version
├── templates/
│   └── index.html         # Web interface
├── requirements.txt
├── run.bat                # Quick launcher
└── .github/
    └── workflows/
        └── build.yml      # GitHub Actions CI/CD
```

## ⚙️ How It Works

1. Detects connected Bluetooth audio devices
2. Monitors connection status every 3 seconds
3. When device disconnects → Screen turns OFF
4. Move mouse or press key → Screen wakes up

## 🔧 GitHub Actions

The project includes CI/CD that:
- ✅ Tests the code on every push
- 📦 Builds a Windows executable
- 🚀 Creates releases automatically

## 📝 License

MIT License
