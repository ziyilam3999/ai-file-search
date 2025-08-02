#!/usr/bin/env python3
"""
Document Set Switcher for AI File Search

This script automatically discovers document categories from sample_docs subfolders
and allows you to easily switch between them without manual configuration.

Features:
- Auto-discovery of document categories from folder structure
- Dynamic configuration updates
- Automatic watcher setup for new folders

Usage:
    python switch_documents.py <category_name>
    python switch_documents.py all
    python switch_documents.py status
    python switch_documents.py discover
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

import yaml

from core.embedding import Embedder


def discover_document_categories() -> Dict[str, Dict]:
    """Auto-discover document categories from sample_docs folder structure."""
    sample_docs_path = Path("sample_docs")
    categories: Dict[str, Dict] = {}

    if not sample_docs_path.exists():
        print("WARNING: sample_docs folder does not exist")
        return categories

    # Find all subdirectories in sample_docs
    for item in sample_docs_path.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            category_name = item.name

            # Create corresponding extracts folder if it doesn't exist
            extracts_path = Path(f"extracts/{category_name}")
            extracts_path.mkdir(parents=True, exist_ok=True)

            categories[category_name] = {
                "enabled": False,  # Default to disabled
                "paths": [f"sample_docs/{category_name}", f"extracts/{category_name}"],
            }

    return categories


def sync_config_with_filesystem() -> Dict:
    """Synchronize configuration with actual filesystem structure."""
    config_path = Path("prompts/watcher_config.yaml")

    # Load existing config or create default
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = create_default_config()

    # Discover current categories
    discovered_categories = discover_document_categories()

    # Get existing categories and their enabled status
    existing_categories = config.get("document_categories", {})

    # Merge discovered categories with existing enabled status
    updated_categories = {}
    for cat_name, cat_config in discovered_categories.items():
        if cat_name in existing_categories:
            # Preserve existing enabled status
            cat_config["enabled"] = existing_categories[cat_name].get(
                "enabled", True
            )  # Default to True
        else:
            # New categories default to enabled for seamless experience
            cat_config["enabled"] = True
        updated_categories[cat_name] = cat_config

    # Update config
    config["document_categories"] = updated_categories

    # Ensure watch_directories includes sample_docs and extracts
    watch_dirs = set(config.get("watch_directories", []))
    watch_dirs.update(["sample_docs", "extracts"])
    config["watch_directories"] = list(watch_dirs)

    # Save updated configuration
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)

    print(f"Configuration synchronized with filesystem")
    return config


def create_default_config() -> Dict:
    """Create a comprehensive default configuration."""
    return {
        "document_categories": {},
        "watch_directories": ["sample_docs", "extracts"],
        "file_patterns": {
            "include": ["*.txt", "*.pdf", "*.docx", "*.md", "*.html", "*.rtf"],
            "ignore": [
                "*.tmp",
                "*.log",
                "*.pyc",
                "__pycache__",
                ".git",
                "*.swp",
                "*.bak",
            ],
        },
        "timing": {
            "debounce_seconds": 5,
            "max_wait_seconds": 30,
            "nightly_reindex_time": "02:00",
        },
        "indexing": {
            "incremental_updates": True,
            "backup_before_update": True,
            "batch_size": 50,
        },
        "logging": {
            "level": "INFO",
            "file": "logs/watcher.log",
            "console_output": True,
            "retention": "1 week",
            "rotation": "1 day",
        },
        "performance": {"max_memory_mb": 1024, "worker_threads": 2},
        "monitoring": {"health_check_interval": 300, "stats_interval": 3600},
    }


def get_available_categories() -> List[str]:
    """Get list of all available document categories."""
    config = sync_config_with_filesystem()
    return list(config.get("document_categories", {}).keys())


def update_config(category: str) -> None:
    """Update the watcher configuration to enable/disable document categories."""
    # First sync with filesystem to get latest structure
    config = sync_config_with_filesystem()
    config_path = Path("prompts/watcher_config.yaml")

    available_categories = list(config.get("document_categories", {}).keys())

    if category == "all":
        # Enable all categories
        for cat_name in available_categories:
            config["document_categories"][cat_name]["enabled"] = True
        print(
            f"SUCCESS: Switched to all documents ({len(available_categories)} categories)"
        )

    elif category in available_categories:
        # Enable selected category, disable others
        for cat_name in available_categories:
            config["document_categories"][cat_name]["enabled"] = cat_name == category
        print(f"SUCCESS: Switched to '{category}' documents")

    else:
        print(f"ERROR: Unknown category: {category}")
        print(f"Available categories: {', '.join(available_categories + ['all'])}")
        return

    # Save updated configuration
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)

    print(f"Configuration updated in {config_path}")


def rebuild_index(category: str) -> None:
    """Rebuild the search index for the selected document category."""
    print("Rebuilding search index...")

    # Sync config first to get latest categories
    config = sync_config_with_filesystem()
    available_categories = list(config.get("document_categories", {}).keys())

    # Determine which extracts folder(s) to use
    if category == "all":
        extracts_paths = []
        for cat_name in available_categories:
            if config["document_categories"][cat_name].get("enabled", False):
                extracts_paths.append(Path(f"extracts/{cat_name}"))

        if not extracts_paths:
            print("WARNING: No enabled categories found")
            return

        # For "all", use the root extracts folder and combine all enabled categories
        extracts_path = Path("extracts")

    elif category in available_categories:
        extracts_path = Path(f"extracts/{category}")
    else:
        print(f"ERROR: Cannot rebuild index for unknown category: {category}")
        print(f"Available categories: {', '.join(available_categories + ['all'])}")
        return

    # Check if extracts folder exists and has content
    if not extracts_path.exists():
        print(f"WARNING: Extracts folder does not exist: {extracts_path}")
        print("You may need to extract documents first.")
        return

    # Count files in extracts folder
    txt_files = list(extracts_path.glob("**/*.txt"))
    if not txt_files:
        print(f"WARNING: No .txt files found in {extracts_path}")
        print("You may need to extract documents first.")
        return

    print(f"Found {len(txt_files)} document(s) to index")

    # Rebuild index
    try:
        embedder = Embedder()
        embedder.build_index(extracts_path=extracts_path)
        print("SUCCESS: Index rebuilt successfully!")

    except Exception as e:
        print(f"ERROR: Error rebuilding index: {e}")


def show_status() -> None:
    """Show current configuration status with auto-discovery."""
    # Sync with filesystem first
    config = sync_config_with_filesystem()

    print("\nCurrent Document Categories Status:")
    print("=" * 60)

    categories = config.get("document_categories", {})
    if not categories:
        print("No document categories found in sample_docs/")
        print("Create subfolders in sample_docs/ to organize your documents")
        return

    enabled_count = 0
    total_documents = 0

    for name, settings in categories.items():
        enabled = settings.get("enabled", False)
        status = "ENABLED" if enabled else "DISABLED"
        print(f"{name:25} {status}")

        if enabled:
            enabled_count += 1

        # Count documents in each category
        doc_count = 0
        for path_str in settings.get("paths", []):
            path = Path(path_str)
            if path.exists():
                txt_files = list(path.glob("**/*.txt"))
                if "extracts" in str(path):
                    doc_count = len(txt_files)
                    total_documents += doc_count
                    folder_status = "DOCS" if doc_count > 0 else "EMPTY"
                    print(f"{'':27} {folder_status} {doc_count} documents in {path}")
                elif "sample_docs" in str(path):
                    source_files = list(path.glob("**/*"))
                    source_count = len([f for f in source_files if f.is_file()])
                    folder_status = "FILES" if source_count > 0 else "EMPTY"
                    print(
                        f"{'':27} {folder_status} {source_count} source files in {path}"
                    )

    print("=" * 60)
    print(f"Summary: {enabled_count}/{len(categories)} categories enabled")
    print(f"Total indexed documents: {total_documents}")
    print()


def discover_and_show() -> None:
    """Discover categories and show what was found."""
    print("Discovering document categories from sample_docs/...")

    discovered = discover_document_categories()

    if not discovered:
        print("ERROR: No document categories found!")
        print("HINT: Create subfolders in sample_docs/ to organize your documents")
        print("   Example: sample_docs/research/, sample_docs/manuals/, etc.")
        return

    print(f"SUCCESS: Discovered {len(discovered)} document categories:")
    for name in discovered.keys():
        sample_path = Path(f"sample_docs/{name}")
        extracts_path = Path(f"extracts/{name}")

        # Count files
        sample_files = (
            len(list(sample_path.glob("**/*"))) if sample_path.exists() else 0
        )
        extract_files = (
            len(list(extracts_path.glob("**/*.txt"))) if extracts_path.exists() else 0
        )

        print(f"  FOLDER: {name}")
        print(f"     └── sample_docs/{name} ({sample_files} files)")
        print(f"     └── extracts/{name} ({extract_files} indexed)")

    print("\nHINT: Use 'python switch_documents.py <category_name>' to switch")
    print("HINT: Use 'python switch_documents.py all' to enable all categories")


def check_watcher_status() -> None:
    """Check if the watcher is running and provide guidance."""
    print("\nWatcher Status Check:")
    print("=" * 40)

    # Check if watcher log exists and is recent
    log_path = Path("logs/watcher.log")
    if log_path.exists():
        import time

        mod_time = log_path.stat().st_mtime
        time_diff = time.time() - mod_time

        if time_diff < 300:  # 5 minutes
            print("STATUS: Watcher appears to be running (recent log activity)")
        else:
            print("STATUS: Watcher may not be running (no recent log activity)")
    else:
        print("STATUS: Watcher not running (no log file found)")

    print("\nTo start the watcher:")
    print("   python run_watcher.py")
    print("\nTo check watcher config:")
    print("   python run_watcher.py --dry-run")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Switch AI File Search document categories with auto-discovery"
    )
    parser.add_argument(
        "category",
        nargs="?",
        help="Document category to switch to ('all', 'status', 'discover', or any discovered category name)",
    )
    parser.add_argument(
        "--no-rebuild", action="store_true", help="Skip rebuilding the search index"
    )

    args = parser.parse_args()

    # If no category provided, show help
    if not args.category:
        print("Auto-discovering available categories...")
        available = get_available_categories()
        if available:
            print(f"Available categories: {', '.join(available)}")
            print("Special commands: all, status, discover")
        else:
            print("No categories found. Use 'discover' to see what's available.")
        print("\nUsage: python switch_documents.py <category_name>")
        return

    # Handle special commands
    if args.category == "status":
        show_status()
        check_watcher_status()
        return
    elif args.category == "discover":
        discover_and_show()
        return

    # Sync filesystem and get available categories
    available_categories = get_available_categories()

    if args.category not in available_categories + ["all"]:
        print(f"ERROR: Unknown category: {args.category}")
        print(f"Available categories: {', '.join(available_categories + ['all'])}")
        print("Use 'python switch_documents.py discover' to see all options")
        return

    # Update configuration
    update_config(args.category)

    # Rebuild index unless skipped
    if not args.no_rebuild:
        rebuild_index(args.category)
    else:
        print("SKIP: Skipping index rebuild")

    print(f"\nSUCCESS: Successfully switched to '{args.category}' documents!")
    print("You can now use the AI File Search with the selected document set.")


if __name__ == "__main__":
    main()
