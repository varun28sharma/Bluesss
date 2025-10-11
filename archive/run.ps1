# BlueLock - Optimized PowerShell Launcher
param([switch]$NoStats)

$Host.UI.RawUI.WindowTitle = "BlueLock - Optimized"
Set-Location $PSScriptRoot

Write-Host "🔐 Starting BlueLock - Optimized Edition..." -ForegroundColor Cyan
Write-Host ""

# Check virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate environment and run
try {
    .\.venv\Scripts\Activate.ps1
    python bluelock.py
} catch {
    Write-Host "❌ Error running BlueLock: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "👋 BlueLock stopped." -ForegroundColor Green
    if (-not $NoStats) {
        Read-Host "Press Enter to exit"
    }
}