@echo off
:: AI File Search - Windows Launcher
:: Double-click to start the application

title AI File Search
cd /d "%~dp0"

echo.
echo ========================================
echo    AI File Search - Starting...
echo ========================================
echo.

:: Check if poetry is available
where poetry >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Poetry not found. Please run the installer first.
    echo        installers\install_windows.ps1
    pause
    exit /b 1
)

:: Start the file watcher in background
echo Starting file watcher...
start /b poetry run python smart_watcher.py start >nul 2>&1

:: Launch the main application
echo Launching AI File Search...
echo.
echo First launch may take 30-60 seconds to load AI models.
echo Close this window to stop the application.
echo.

poetry run python run_app.py

:: Stop watcher on exit
poetry run python smart_watcher.py stop >nul 2>&1
