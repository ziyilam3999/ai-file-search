#!/usr/bin/env python3
"""
Complete Setup for AI File Search with Zero-Config Smart Watcher

This script sets up everything you need for the best AI File Search experience:
- Installs required dependencies
- Sets up smart watcher with auto-discovery
- Configures default "watch everything" behavior
- Creates helpful documentation

Run this once to get everything working!
"""

import subprocess
import sys
from pathlib import Path


def install_dependencies():
    """Install required Python packages."""
    print("Installing required dependencies...")

    required_packages = [
        "psutil",  # For process management in smart watcher
        "pyyaml",  # Already installed but ensure it's available
    ]

    for package in required_packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"[OK] {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"[ERROR] Failed to install {package}")
            return False

    return True


def setup_folders():
    """Ensure all required folders exist."""
    print("Setting up folder structure...")

    folders = ["ai_search_docs", "extracts", "logs", "prompts"]

    for folder in folders:
        Path(folder).mkdir(exist_ok=True)
        print(f"[OK] Created/verified {folder}/")

    return True


def create_quick_start_guide():
    """Create a comprehensive quick start guide."""
    guide_content = """
    # AI File Search - Complete User Guide

Quick Start (30 seconds)
1. Start the smart watcher (watches ALL folders automatically):
python smart_watcher.py start

2. Add your documents to any folder in ai_search_docs/:
ai_search_docs/
├── my_research/      # Create any folder name
├── work_docs/        # Add your files here
└── personal/         # System auto-discovers everything!

3. Start searching with the web interface:
python -m streamlit run ui/app.py

Open: http://localhost:8501

Key Features
- Zero Configuration
- Add any folder to ai_search_docs/ - it's automatically discovered
- All folders watched by default - no manual setup needed
- Real-time indexing - changes appear in search within seconds

Smart Watcher Commands
python smart_watcher.py start     # Start watching (recommended)
python smart_watcher.py stop      # Stop watching
python smart_watcher.py status    # Check if running + show details
python smart_watcher.py restart   # Restart the watcher

Category Management (Optional)
python switch_documents.py discover  # See all auto-discovered categories
python switch_documents.py status    # Check what's enabled
python switch_documents.py research  # Focus search on 'research' folder only
python switch_documents.py all       # Search everything (default)

Folder Structure
Your project should look like this:
ai_search_docs/
├── my_research/      # Create any folder name
├── work_docs/        # Add your files here
└── personal/         # System auto-discovers everything!
extracts/             # Where AI extracts are saved
logs/                 # Logs for smart watcher and AI
prompts/              # Custom prompts for AI search

How It Works
1. Drop files anywhere in ai_search_docs/subfolders/
2. Watcher detects changes automatically
3. AI extracts and indexes content
4. Search with citations works immediately

Troubleshooting
Watcher not starting?
python smart_watcher.py status  # Check what's wrong
python run_watcher.py --dry-run # Test configuration

Documents not appearing in search?
python switch_documents.py status  # Check if category is enabled
python smart_watcher.py restart    # Restart the watcher

Pro Tips
1. Organize by purpose: Create folders like research/, manuals/, contracts/
2. Use descriptive names: Folder names become searchable categories
3. Mixed file types: PDFs, Word docs, text files all work
4. Nested folders: docs/2024/projects/ structures are fully supported
5. Real-time: No need to restart anything when adding files

You're All Set!
The AI File Search is now running with zero-config smart watching. Just add documents and start searching!

Happy Searching!
"""

    try:
        with open("QUICK_START.md", "w", encoding="utf-8") as guide_file:
            guide_file.write(guide_content)
            print("[OK] Quick start guide created: QUICK_START.md")

        guide_path = Path("COMPLETE_USER_GUIDE.md")
        with open(guide_path, "w", encoding="utf-8") as f:
            f.write(guide_content)

        print(f"[OK] Created comprehensive guide: {guide_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Error creating guides: {e}")
        return False


def run_initial_setup():
    """Run the initial setup for zero-config experience."""
    print("Running initial setup for zero-config experience...")

    try:
        # Import and run discovery to set up defaults
        from switch_documents import sync_config_with_filesystem

        config = sync_config_with_filesystem()

        # Show what was discovered
        categories = config.get("document_categories", {})
        if categories:
            print(f"[OK] Auto-discovered {len(categories)} document categories")
            for name in categories.keys():
                print(f"   - {name}")
        else:
            print(
                "[INFO] No categories found yet - add folders to ai_search_docs/ to get started"
            )

        return True

    except Exception as e:
        print(f"[WARN] Initial setup completed with minor issues: {e}")
        return True  # Non-critical


def main():
    """Main setup routine."""
    print("AI File Search Complete Setup")
    print("=" * 50)
    print("Setting up zero-configuration smart watcher experience...")
    print()

    steps = [
        ("Installing dependencies", install_dependencies),
        ("Setting up folders", setup_folders),
        ("Creating user guide", create_quick_start_guide),
        ("Running initial setup", run_initial_setup),
    ]

    for description, func in steps:
        print(f"{description}...")
        if not func():
            print(f"[ERROR] Setup failed at: {description}")
            return False
        print()

    print("Setup Complete!")
    print("=" * 50)
    print()
    print("Next Steps:")
    print("1. Start the smart watcher:")
    print("   python smart_watcher.py start")
    print()
    print("2. Add your documents to ai_search_docs/ subfolders")
    print()
    print("3. Start searching with the web interface:")
    print("   python -m streamlit run ui/app.py")
    print()
    print("Read COMPLETE_USER_GUIDE.md for full instructions!")
    print()
    print("Your AI File Search is ready for zero-config operation!")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
