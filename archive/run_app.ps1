# BlueLock Desktop App Launcher
param([switch]$Install, [switch]$Dev)

$Host.UI.RawUI.WindowTitle = "BlueLock Desktop App"
Set-Location $PSScriptRoot

Write-Host "🔐 BlueLock Desktop App" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

# Check virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        Write-Host "Please make sure Python 3.8+ is installed" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate environment
Write-Host "Activating environment..." -ForegroundColor Green
.\.venv\Scripts\Activate.ps1

# Install/update dependencies
if ($Install -or -not (Test-Path ".venv\Lib\site-packages\customtkinter")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt --quiet --disable-pip-version-check
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Some dependencies may not have installed correctly" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🚀 Starting BlueLock Desktop App..." -ForegroundColor Green
Write-Host ""

# Run the application
try {
    if ($Dev) {
        # Development mode - show console
        python bluelock_app.py
    } else {
        # Production mode - hide console (optional)
        python bluelock_app.py
    }
} catch {
    Write-Host "❌ Application failed to start: $_" -ForegroundColor Red
} finally {
    if (-not $Dev) {
        Read-Host "Press Enter to exit"
    }
}