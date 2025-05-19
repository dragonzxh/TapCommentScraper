# PowerShell Version of Steam Comment Crawler Startup Script (Edge Browser)
# This script supports running from UNC paths and uses Microsoft Edge browser

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Get script directory
$scriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
Set-Location -Path $scriptDir

Write-Host "========================================="
Write-Host "  Steam Comment Crawler - Edge Browser   "
Write-Host "========================================="
Write-Host ""

# Check if path is a UNC path
if ($scriptDir -like "\\*") {
    Write-Host "UNC path detected: $scriptDir" -ForegroundColor Yellow
    Write-Host "PowerShell supports UNC paths, continuing..." -ForegroundColor Green
    Write-Host ""
}

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3") {
        Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "Error: Python 3 not detected. Please install Python 3 first." -ForegroundColor Red
        Write-Host "You can download it from https://www.python.org/downloads/" -ForegroundColor Yellow
        Read-Host "Press any key to exit..."
        exit 1
    }
} catch {
    Write-Host "Error: Python not detected. Please install Python first." -ForegroundColor Red
    Write-Host "You can download it from https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press any key to exit..."
    exit 1
}

# Check if virtual environment exists, create if not
if (-not (Test-Path "venv")) {
    Write-Host "=== First Run Setup ===" -ForegroundColor Cyan
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    
    if (-not (Test-Path "venv")) {
        Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press any key to exit..."
        exit 1
    }
    
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    if ($PSVersionTable.PSVersion.Major -ge 5) {
        & .\venv\Scripts\Activate.ps1
    } else {
        Write-Host "Error: PowerShell version too low to activate virtual environment" -ForegroundColor Red
        Read-Host "Press any key to exit..."
        exit 1
    }
    
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install --upgrade pip
    pip install flask selenium beautifulsoup4 requests webdriver-manager
} else {
    Write-Host "Existing virtual environment detected, activating..." -ForegroundColor Green
    if ($PSVersionTable.PSVersion.Major -ge 5) {
        & .\venv\Scripts\Activate.ps1
    } else {
        Write-Host "Error: PowerShell version too low to activate virtual environment" -ForegroundColor Red
        Read-Host "Press any key to exit..."
        exit 1
    }
}

# Ensure output and cookies directories exist
if (-not (Test-Path "output")) { New-Item -ItemType Directory -Path "output" | Out-Null }
if (-not (Test-Path "cookies")) { New-Item -ItemType Directory -Path "cookies" | Out-Null }

# Check if Edge browser is installed
try {
    $edgePath = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe').'(Default)'
    if ($edgePath) {
        Write-Host "Microsoft Edge browser detected: $edgePath" -ForegroundColor Green
    }
} catch {
    Write-Host "Warning: Microsoft Edge browser not detected. The crawler may not work properly." -ForegroundColor Yellow
    Write-Host "Please install Microsoft Edge browser before running this script." -ForegroundColor Yellow
    $choice = Read-Host "Continue anyway? [y/n]"
    if ($choice -ne "y") {
        Write-Host "Operation cancelled." -ForegroundColor Red
        Read-Host "Press any key to exit..."
        exit 1
    }
}

# Install webdriver-manager if not already installed
try {
    $webdriverManager = pip show webdriver-manager
    if (-not $webdriverManager) {
        Write-Host "Installing webdriver-manager..." -ForegroundColor Yellow
        pip install webdriver-manager
    } else {
        Write-Host "webdriver-manager already installed." -ForegroundColor Green
    }
} catch {
    Write-Host "Installing webdriver-manager..." -ForegroundColor Yellow
    pip install webdriver-manager
}

# Set environment variable to skip login check
$env:SKIP_LOGIN_CHECK = 1

# Start Flask server
Write-Host "Starting web server with Edge browser support..." -ForegroundColor Cyan
Set-Location -Path $scriptDir
$pythonProcess = Start-Process -FilePath "python" -ArgumentList "crawler_web_start.py --browser edge" -PassThru -NoNewWindow

# Wait for server to start
Write-Host "Waiting for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Open browser to access Steam page
Write-Host "Opening web page..." -ForegroundColor Green
Start-Process "http://localhost:5000/steam"

Write-Host ""
Write-Host "Steam Comment Crawler (Edge Browser) has started!" -ForegroundColor Green
Write-Host "Please operate in the browser. Close this window to stop the server." -ForegroundColor Cyan
Write-Host ""

Read-Host "Press any key to stop the server..."
Write-Host "Stopping server..." -ForegroundColor Yellow

# Stop all Python processes
Stop-Process -Id $pythonProcess.Id -Force -ErrorAction SilentlyContinue
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "Server stopped." -ForegroundColor Green 