# BlueLock App Builder
# Creates standalone executable using PyInstaller

param([switch]$Clean, [switch]$Debug)

Write-Host "🔧 BlueLock App Builder" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

Set-Location $PSScriptRoot

# Activate virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    .\.venv\Scripts\Activate.ps1
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "❌ Virtual environment not found. Run run_app.ps1 first." -ForegroundColor Red
    exit 1
}

# Install PyInstaller if needed
Write-Host "📦 Checking PyInstaller..." -ForegroundColor Yellow
pip show pyinstaller > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Clean previous builds
if ($Clean -and (Test-Path "dist")) {
    Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "dist", "build" -ErrorAction SilentlyContinue
}

# Build parameters
$buildArgs = @(
    "bluelock_app.py"
    "--name=BlueLock"
    "--windowed"  # No console window
    "--onefile"   # Single executable
    "--icon=app_icon.ico"  # App icon (if exists)
    "--add-data=settings.py;."
    "--hidden-import=customtkinter"
    "--hidden-import=pystray"
    "--hidden-import=PIL"
    "--hidden-import=plyer"
    "--hidden-import=bleak"
)

if ($Debug) {
    $buildArgs += "--debug=all"
    $buildArgs = $buildArgs | Where-Object { $_ -ne "--windowed" }  # Keep console for debug
}

Write-Host "🔨 Building BlueLock executable..." -ForegroundColor Green
Write-Host "This may take several minutes..." -ForegroundColor Yellow

# Run PyInstaller
& pyinstaller @buildArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Build completed successfully!" -ForegroundColor Green
    Write-Host "📁 Executable location: dist\BlueLock.exe" -ForegroundColor Cyan
    Write-Host ""
    
    # Check file size
    $exePath = "dist\BlueLock.exe"
    if (Test-Path $exePath) {
        $size = (Get-Item $exePath).Length / 1MB
        Write-Host "📊 File size: $([math]::Round($size, 1)) MB" -ForegroundColor Yellow
        
        Write-Host ""
        Write-Host "🎯 To distribute BlueLock:" -ForegroundColor Cyan
        Write-Host "   1. Copy dist\BlueLock.exe to target computer" -ForegroundColor White
        Write-Host "   2. Run BlueLock.exe (no installation needed)" -ForegroundColor White
        Write-Host "   3. App will start with GUI interface" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "❌ Build failed!" -ForegroundColor Red
    Write-Host "Check the output above for errors" -ForegroundColor Yellow
}

Read-Host "Press Enter to continue"