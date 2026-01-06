#!/bin/bash
# AI File Search - Linux Installer
# 
# One-click installer for AI File Search on Linux (Ubuntu/Debian/Fedora/Arch).
# Installs Python, Poetry, dependencies, and downloads the AI model.
#
# Run with: chmod +x install_linux.sh && ./install_linux.sh

set -e

# Configuration
PYTHON_MIN_VERSION="3.12"
MODEL_REPO="Qwen/Qwen2.5-1.5B-Instruct-GGUF"
MODEL_FILE="qwen2.5-1.5b-instruct-q4_k_m.gguf"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "========================================"
echo "   AI File Search - Linux Installer    "
echo "========================================"
echo ""

cd "$PROJECT_DIR"

# Detect package manager
detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    elif command -v zypper &> /dev/null; then
        echo "zypper"
    else
        echo "unknown"
    fi
}

PKG_MANAGER=$(detect_package_manager)

# -----------------------------------------------------------------------------
# Step 1: Install System Dependencies
# -----------------------------------------------------------------------------
echo -e "\033[33m[1/5] Installing system dependencies...\033[0m"

case $PKG_MANAGER in
    apt)
        sudo apt-get update
        sudo apt-get install -y python3.12 python3.12-venv python3-pip curl git
        ;;
    dnf)
        sudo dnf install -y python3.12 python3-pip curl git
        ;;
    pacman)
        sudo pacman -Sy --noconfirm python python-pip curl git
        ;;
    zypper)
        sudo zypper install -y python312 python3-pip curl git
        ;;
    *)
        echo "  Unknown package manager. Please install Python 3.12+ manually."
        ;;
esac

echo -e "\033[32m  System dependencies installed.\033[0m"

# -----------------------------------------------------------------------------
# Step 2: Check Python
# -----------------------------------------------------------------------------
echo ""
echo -e "\033[33m[2/5] Checking Python installation...\033[0m"

PYTHON_CMD=""
for cmd in python3.12 python3 python; do
    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if [[ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$version" | sort -V | head -1)" == "$PYTHON_MIN_VERSION" ]]; then
            PYTHON_CMD=$cmd
            echo -e "\033[32m  Found: Python $version\033[0m"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo -e "\033[31m  Python $PYTHON_MIN_VERSION+ not found. Please install it manually.\033[0m"
    exit 1
fi

# -----------------------------------------------------------------------------
# Step 3: Install Poetry
# -----------------------------------------------------------------------------
echo ""
echo -e "\033[33m[3/5] Checking Poetry installation...\033[0m"

if ! command -v poetry &> /dev/null; then
    echo "  Installing Poetry..."
    curl -sSL https://install.python-poetry.org | $PYTHON_CMD -
    
    # Add Poetry to PATH
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "\033[32m  Poetry installed.\033[0m"
else
    echo -e "\033[32m  Found: $(poetry --version)\033[0m"
fi

# -----------------------------------------------------------------------------
# Step 4: Install Dependencies
# -----------------------------------------------------------------------------
echo ""
echo -e "\033[33m[4/5] Installing Python dependencies...\033[0m"
echo "  This may take 2-5 minutes on first run."

poetry install --no-interaction --no-root

echo -e "\033[32m  Dependencies installed.\033[0m"

# -----------------------------------------------------------------------------
# Step 5: Download AI Model
# -----------------------------------------------------------------------------
echo ""
echo -e "\033[33m[5/5] Downloading AI model (~1.1GB)...\033[0m"

MODEL_DIR="$PROJECT_DIR/ai_models"
MODEL_PATH="$MODEL_DIR/$MODEL_FILE"

mkdir -p "$MODEL_DIR"

if [[ -f "$MODEL_PATH" ]]; then
    echo -e "\033[32m  Model already exists: $MODEL_FILE\033[0m"
else
    echo "  Downloading from Hugging Face Hub..."
    echo "  This will take a few minutes depending on your connection."
    
    # Install huggingface-hub if not present
    poetry run pip install huggingface-hub --quiet
    
    # Download model
    poetry run huggingface-cli download "$MODEL_REPO" "$MODEL_FILE" --local-dir "$MODEL_DIR" --local-dir-use-symlinks False
    
    if [[ -f "$MODEL_PATH" ]]; then
        echo -e "\033[32m  Model downloaded successfully.\033[0m"
    else
        echo -e "\033[31m  Model download failed. Please check your internet connection.\033[0m"
        exit 1
    fi
fi

# -----------------------------------------------------------------------------
# Run Setup
# -----------------------------------------------------------------------------
echo ""
echo "Running initial setup..."

poetry run python complete_setup.py

echo -e "\033[32m  Setup complete.\033[0m"

# -----------------------------------------------------------------------------
# Create Desktop Entry (optional)
# -----------------------------------------------------------------------------
DESKTOP_DIR="$HOME/.local/share/applications"
if [[ -d "$DESKTOP_DIR" ]]; then
    cat > "$DESKTOP_DIR/ai-file-search.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AI File Search
Comment=Local document search with AI
Exec=$PROJECT_DIR/AI-File-Search.sh
Icon=system-search
Terminal=false
Categories=Utility;
EOF
    echo -e "\033[32m  Desktop entry created.\033[0m"
fi

# Make launcher executable
chmod +x "$PROJECT_DIR/AI-File-Search.sh" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Done!
# -----------------------------------------------------------------------------
echo ""
echo "========================================"
echo -e "\033[32m   Installation Complete!              \033[0m"
echo "========================================"
echo ""
echo -e "\033[36mTo start AI File Search:\033[0m"
echo "  1. Run: ./AI-File-Search.sh"
echo "  2. Or find 'AI File Search' in your applications menu"
echo ""
echo "First launch may take 30-60 seconds to load AI models."
echo ""
