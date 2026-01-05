#!/bin/bash
# AI File Search - Linux Launcher

cd "$(dirname "$0")"

echo ""
echo "========================================"
echo "   AI File Search - Starting...        "
echo "========================================"
echo ""

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    # Try adding Poetry to PATH
    export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v poetry &> /dev/null; then
    echo "ERROR: Poetry not found. Please run the installer first."
    echo "       ./installers/install_linux.sh"
    read -p "Press Enter to exit..."
    exit 1
fi

# Start the file watcher in background
echo "Starting file watcher..."
poetry run python smart_watcher.py start &>/dev/null &

# Launch the main application
echo "Launching AI File Search..."
echo ""
echo "First launch may take 30-60 seconds to load AI models."
echo "Close this window to stop the application."
echo ""

poetry run python run_app.py

# Stop watcher on exit
poetry run python smart_watcher.py stop &>/dev/null
