#!/usr/bin/env python3
"""
Document Category Management for AI File Search

This module manages document categories and configuration for the AI file search system.
It supports Option 1 Architecture: ai_search_docs → extracts → index
"""

import os
from pathlib import Path
from typing import Dict, List, Set

import yaml


def get_existing_categories() -> Set[str]:
    """Get existing category directories from ai_search_docs."""
    ai_search_docs_path = Path("ai_search_docs")
    if not ai_search_docs_path.exists():
        return set()

    categories = set()
    for item in ai_search_docs_path.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            categories.add(item.name)

    return categories


def create_default_category_config(category_name: str) -> Dict:
    """Create default configuration for a category (Option 1: ai_search_docs only)."""
    return {
        "enabled": True,
        "paths": [
            f"ai_search_docs/{category_name}"
        ],  # Only watch ai_search_docs (Option 1)
    }


def load_existing_config() -> Dict:
    """Load existing configuration or create default."""
    config_path = Path("prompts/watcher_config.yaml")

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading config: {e}")

    return {}


def sync_config_with_filesystem() -> Dict:
    """Sync configuration with filesystem categories (Option 1 Architecture)."""
    config_path = Path("prompts/watcher_config.yaml")

    # Load existing config
    config = load_existing_config()

    # Ensure document_categories section exists
    if "document_categories" not in config:
        config["document_categories"] = {}

    # Get existing categories from filesystem
    existing_categories = get_existing_categories()

    # Add new categories found in filesystem
    for category in existing_categories:
        if category not in config["document_categories"]:
            config["document_categories"][category] = create_default_category_config(
                category
            )
            print(f"✅ Added new category: {category}")

    # Set file patterns if not exists
    if "file_patterns" not in config:
        config["file_patterns"] = {
            "include": ["*.txt", "*.pdf", "*.docx", "*.md"],
            "ignore": [
                "*.tmp",
                "*.log",
                "*.pyc",
                "__pycache__",
                ".git",
                "*.swp",
                "*.bak",
            ],
        }

    # OPTION 1 ARCHITECTURE: Only watch ai_search_docs
    config["watch_directories"] = ["ai_search_docs"]

    # Save updated configuration
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return config


def get_default_config() -> Dict:
    """Get default configuration for Option 1 Architecture."""
    return {
        "document_categories": {},
        "file_patterns": {
            "include": ["*.txt", "*.pdf", "*.docx", "*.md"],
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
        "watch_directories": ["ai_search_docs"],  # Option 1: Only watch ai_search_docs
    }


def create_category(category_name: str) -> bool:
    """Create a new document category."""
    try:
        # Create directory structure
        sample_dir = Path("ai_search_docs") / category_name
        extract_dir = Path("extracts") / category_name

        sample_dir.mkdir(parents=True, exist_ok=True)
        extract_dir.mkdir(parents=True, exist_ok=True)

        # Update configuration
        sync_config_with_filesystem()

        print(f"✅ Category '{category_name}' created successfully")
        print(f"📁 Add files to: ai_search_docs/{category_name}/")
        print(f"📁 Extracts will go to: extracts/{category_name}/")

        return True

    except Exception as e:
        print(f"❌ Error creating category '{category_name}': {e}")
        return False


def update_config(category_name: str, enabled: bool = True) -> bool:
    """Update configuration for a specific category."""
    try:
        config = sync_config_with_filesystem()
        config_path = Path("prompts/watcher_config.yaml")

        if category_name not in config["document_categories"]:
            config["document_categories"][category_name] = (
                create_default_category_config(category_name)
            )

        config["document_categories"][category_name]["enabled"] = enabled

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        status = "enabled" if enabled else "disabled"
        print(f"✅ Category '{category_name}' {status}")

        return True

    except Exception as e:
        print(f"❌ Error updating category '{category_name}': {e}")
        return False


def list_categories() -> Dict:
    """List all document categories and their status."""
    config = sync_config_with_filesystem()

    categories = config.get("document_categories", {})

    print("📋 Document Categories (Option 1 Architecture):")
    print("=" * 50)

    if not categories:
        print("   No categories found")
        return {}

    for name, settings in categories.items():
        enabled = "✅ ENABLED" if settings.get("enabled", True) else "❌ DISABLED"
        paths = settings.get("paths", [])

        print(f"   {name}: {enabled}")
        for path in paths:
            exists = "✅" if Path(path).exists() else "❌"
            print(f"      {exists} {path}")
        print()

    print(f"📁 Watch directories: {config.get('watch_directories', [])}")

    return categories


def main():
    """Main function for command-line usage."""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python switch_documents.py list")
        print("  python switch_documents.py create <category_name>")
        print("  python switch_documents.py enable <category_name>")
        print("  python switch_documents.py disable <category_name>")
        print("  python switch_documents.py sync")
        return

    command = sys.argv[1].lower()

    if command == "list":
        list_categories()
    elif command == "sync":
        sync_config_with_filesystem()
        print("✅ Configuration synchronized with filesystem")
    elif command == "create" and len(sys.argv) > 2:
        create_category(sys.argv[2])
    elif command == "enable" and len(sys.argv) > 2:
        update_config(sys.argv[2], True)
    elif command == "disable" and len(sys.argv) > 2:
        update_config(sys.argv[2], False)
    else:
        print("❌ Invalid command or missing category name")


if __name__ == "__main__":
    main()
