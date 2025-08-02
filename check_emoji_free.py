#!/usr/bin/env python3
"""
Emoji Detection Script

This script scans important codebase files for emoji characters to ensure cross-platform compatibility.
Run this before committing code changes to validate emoji-free requirement.

Usage:
    python check_emoji_free.py

Expected Output:
    SUCCESS: Codebase is emoji-free (or list of files with emojis)
"""

import os
import re
import sys
from pathlib import Path


def has_emoji(text):
    """Check if text contains emoji characters."""
    # Unicode ranges for common emoji
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\U00002702-\U000027b0"  # dingbats
        "\U000024c2-\U0001f251"  # enclosed characters
        "]+",
        flags=re.UNICODE,
    )
    return bool(emoji_pattern.search(text))


def scan_file(file_path):
    """Scan a file for emoji characters."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if has_emoji(content):
                # Find line numbers with emojis
                lines_with_emojis = []
                for line_num, line in enumerate(content.split("\n"), 1):
                    if has_emoji(line):
                        lines_with_emojis.append((line_num, line.strip()))
                return lines_with_emojis
    except (UnicodeDecodeError, PermissionError):
        # Skip binary files or files we can't read
        pass
    return []


def get_important_files():
    """Get list of important files to check for emojis."""
    project_root = Path(__file__).parent
    important_files = []

    # Core Python files
    core_patterns = ["core/*.py", "ui/*.py", "daemon/*.py", "tests/*.py"]

    # Root-level important files
    root_files = [
        "cli.py",
        "complete_setup.py",
        "smart_watcher.py",
        "switch_documents.py",
        "validate_embedder_format.py",
        "check_emoji_free.py",
        "setup_auto_discovery.py",
        "run_watcher.py",
    ]

    # Important documentation
    doc_files = [
        "README.md",
        "QUICK_START.md",
        "COMPLETE_USER_GUIDE.md",
        "docs/EMBEDDER_API_SPECIFICATION.md",
        "docs/CODE_STYLE_GUIDELINES.md",
        "prompts/*.md",
        "prompts/*.yaml",
    ]

    # Configuration files
    config_files = ["pyproject.toml", "package.json", "poetry.toml"]

    # Collect files from patterns
    all_patterns = core_patterns + doc_files + config_files

    for pattern in all_patterns:
        for file_path in project_root.glob(pattern):
            if file_path.is_file():
                important_files.append(file_path)

    # Add root files
    for file_name in root_files:
        file_path = project_root / file_name
        if file_path.exists() and file_path.is_file():
            important_files.append(file_path)

    return important_files


def scan_important_files():
    """Scan important files for emoji characters."""
    files_with_emojis = {}

    print("Scanning important files for emoji characters...")
    print("=" * 50)

    important_files = get_important_files()

    print(f"Checking {len(important_files)} important files...")

    for file_path in important_files:
        emoji_lines = scan_file(file_path)
        if emoji_lines:
            rel_path = file_path.relative_to(Path(__file__).parent)
            files_with_emojis[str(rel_path)] = emoji_lines

    return files_with_emojis


def main():
    """Main emoji detection entry point."""
    print("AI File Search - Important Files Emoji Detection")
    print("=" * 50)

    files_with_emojis = scan_important_files()

    if not files_with_emojis:
        print("SUCCESS: Important files are emoji-free!")
        print("SUCCESS: Cross-platform compatibility maintained")
        print("SUCCESS: Subprocess operations will work reliably")
        print("SUCCESS: Professional code standards met")
        print()
        print("FILES CHECKED:")
        print("- Core Python modules (core/, ui/, daemon/, tests/)")
        print("- Main scripts and utilities")
        print("- Critical documentation (README, guides, specs)")
        print("- Configuration files")
        return True
    else:
        print("ERROR: Found emoji characters in important files:")
        print()

        for file_path, emoji_lines in files_with_emojis.items():
            print(f"FILE: {file_path}")
            for line_num, line in emoji_lines:
                print(f"   Line {line_num}: {line[:80]}...")
            print()

        print("REQUIRED ACTIONS:")
        print(
            "1. Replace emojis with text prefixes (see docs/CODE_STYLE_GUIDELINES.md)"
        )
        print("2. Use descriptive text like STARTING, SUCCESS, ERROR instead")
        print("3. Re-run this script to verify fixes")
        print()
        print("See docs/CODE_STYLE_GUIDELINES.md for replacement guidelines")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
