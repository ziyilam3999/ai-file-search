#!/bin/bash
# AI File Search - macOS Installer
# 
# One-click installer for AI File Search on macOS.
# Installs Homebrew (if needed), Python, Poetry, dependencies, and downloads the AI model.
#
# Run with: chmod +x install_macos.sh && ./install_macos.sh

set -e

# Configuration
PYTHON_MIN_VERSION="3.12"
MODEL_REPO="Qwen/Qwen2.5-1.5B-Instruct-GGUF"
MODEL_FILE="qwen2.5-1.5b-instruct-q4_k_m.gguf"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "========================================"
echo "   AI File Search - macOS Installer    "
echo "========================================"
echo ""

cd "$PROJECT_DIR"

# -----------------------------------------------------------------------------
# Step 1: Check/Install Homebrew
# -----------------------------------------------------------------------------
echo -e "\033[33m[1/5] Checking Homebrew installation...\033[0m"

if ! command -v brew &> /dev/null; then
    echo "  Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    echo -e "\033[32m  Homebrew installed.\033[0m"
else
    echo -e "\033[32m  Found: $(brew --version | head -1)\033[0m"
fi

# -----------------------------------------------------------------------------
# Step 2: Check/Install Python
# -----------------------------------------------------------------------------
echo ""
echo -e "\033[33m[2/5] Checking Python installation...\033[0m"

PYTHON_CMD=""
for cmd in python3 python; do
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
    echo "  Python $PYTHON_MIN_VERSION+ not found. Installing via Homebrew..."
    brew install python@3.12
    PYTHON_CMD="python3"
    echo -e "\033[32m  Python installed.\033[0m"
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
# Make launcher executable
# -----------------------------------------------------------------------------
chmod +x "$PROJECT_DIR/AI-File-Search.command"

# -----------------------------------------------------------------------------
# Done!
# -----------------------------------------------------------------------------
echo ""
echo "========================================"
echo -e "\033[32m   Installation Complete!              \033[0m"
echo "========================================"
echo ""
echo -e "\033[36mTo start AI File Search:\033[0m"
echo "  1. Double-click 'AI-File-Search.command' in Finder"
echo "  2. Or run: ./AI-File-Search.command"
echo ""
echo "First launch may take 30-60 seconds to load AI models."
echo ""
