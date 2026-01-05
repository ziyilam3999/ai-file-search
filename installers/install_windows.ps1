<# 
.SYNOPSIS
    AI File Search - Windows Installer
.DESCRIPTION
    One-click installer for AI File Search on Windows.
    Installs Python (if needed), Poetry, dependencies, and downloads the AI model.
.NOTES
    Run with: .\install_windows.ps1
    Or right-click > "Run with PowerShell"
#>

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # Faster downloads

# Configuration
$PYTHON_MIN_VERSION = "3.12"
$PYTHON_INSTALLER_URL = "https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"
$MODEL_REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
$MODEL_FILE = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_DIR = Split-Path -Parent $SCRIPT_DIR

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AI File Search - Windows Installer  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PROJECT_DIR

# -----------------------------------------------------------------------------
# Step 1: Check Python
# -----------------------------------------------------------------------------
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python (\d+\.\d+)") {
            $ver = [version]$Matches[1]
            if ($ver -ge [version]$PYTHON_MIN_VERSION) {
                $pythonCmd = $cmd
                Write-Host "  Found: $version" -ForegroundColor Green
                break
            }
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "  Python $PYTHON_MIN_VERSION+ not found." -ForegroundColor Red
    Write-Host ""
    $install = Read-Host "  Install Python 3.12 now? (Y/n)"
    if ($install -ne "n" -and $install -ne "N") {
        Write-Host "  Downloading Python installer..." -ForegroundColor Yellow
        $installerPath = "$env:TEMP\python-installer.exe"
        Invoke-WebRequest -Uri $PYTHON_INSTALLER_URL -OutFile $installerPath
        
        Write-Host "  Running Python installer (please complete the wizard)..." -ForegroundColor Yellow
        Write-Host "  IMPORTANT: Check 'Add Python to PATH' during installation!" -ForegroundColor Magenta
        Start-Process -FilePath $installerPath -Wait
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $pythonCmd = "python"
    } else {
        Write-Host "  Please install Python $PYTHON_MIN_VERSION+ and run this script again." -ForegroundColor Red
        exit 1
    }
}

# -----------------------------------------------------------------------------
# Step 2: Install Poetry
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/5] Checking Poetry installation..." -ForegroundColor Yellow

$poetryInstalled = $false
try {
    $poetryVersion = & poetry --version 2>&1
    if ($poetryVersion -match "Poetry") {
        Write-Host "  Found: $poetryVersion" -ForegroundColor Green
        $poetryInstalled = $true
    }
} catch {}

if (-not $poetryInstalled) {
    Write-Host "  Installing Poetry..." -ForegroundColor Yellow
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | & $pythonCmd -
    
    # Add Poetry to PATH for this session
    $poetryPath = "$env:APPDATA\Python\Scripts"
    if (Test-Path "$env:APPDATA\pypoetry\venv\Scripts\poetry.exe") {
        $poetryPath = "$env:APPDATA\pypoetry\venv\Scripts"
    }
    $env:Path = "$poetryPath;$env:Path"
    Write-Host "  Poetry installed." -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# Step 3: Install Dependencies
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/5] Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "  This may take 2-5 minutes on first run." -ForegroundColor Gray

poetry install --no-interaction
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Failed to install dependencies." -ForegroundColor Red
    exit 1
}
Write-Host "  Dependencies installed." -ForegroundColor Green

# -----------------------------------------------------------------------------
# Step 4: Download AI Model
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/5] Downloading AI model (~1.1GB)..." -ForegroundColor Yellow

$modelDir = Join-Path $PROJECT_DIR "ai_models"
$modelPath = Join-Path $modelDir $MODEL_FILE

if (-not (Test-Path $modelDir)) {
    New-Item -ItemType Directory -Path $modelDir -Force | Out-Null
}

if (Test-Path $modelPath) {
    Write-Host "  Model already exists: $MODEL_FILE" -ForegroundColor Green
} else {
    Write-Host "  Downloading from Hugging Face Hub..." -ForegroundColor Yellow
    Write-Host "  This will take a few minutes depending on your connection." -ForegroundColor Gray
    
    # Install huggingface-hub if not present
    poetry run pip install huggingface-hub --quiet
    
    # Download model using huggingface-cli
    poetry run huggingface-cli download $MODEL_REPO $MODEL_FILE --local-dir $modelDir --local-dir-use-symlinks False
    
    if (Test-Path $modelPath) {
        Write-Host "  Model downloaded successfully." -ForegroundColor Green
    } else {
        Write-Host "  Model download failed. Please check your internet connection." -ForegroundColor Red
        exit 1
    }
}

# -----------------------------------------------------------------------------
# Step 5: Run Setup
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/5] Running initial setup..." -ForegroundColor Yellow

poetry run python complete_setup.py
Write-Host "  Setup complete." -ForegroundColor Green

# -----------------------------------------------------------------------------
# Create Desktop Shortcut
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "Creating desktop shortcut..." -ForegroundColor Yellow

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "AI File Search.lnk"
$targetPath = Join-Path $PROJECT_DIR "AI-File-Search.bat"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $targetPath
$Shortcut.WorkingDirectory = $PROJECT_DIR
$Shortcut.Description = "AI File Search - Local document search with AI"
$Shortcut.Save()

Write-Host "  Shortcut created: $shortcutPath" -ForegroundColor Green

# -----------------------------------------------------------------------------
# Done!
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Installation Complete!              " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start AI File Search:" -ForegroundColor Cyan
Write-Host "  1. Double-click 'AI File Search' on your desktop" -ForegroundColor White
Write-Host "  2. Or run: .\AI-File-Search.bat" -ForegroundColor White
Write-Host ""
Write-Host "First launch may take 30-60 seconds to load AI models." -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"
