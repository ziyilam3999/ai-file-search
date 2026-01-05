#!/usr/bin/env python3
"""
Build Distribution Script for AI File Search

Creates a distributable ZIP file for team members, excluding development files,
virtual environments, AI models (downloaded on first run), and user-specific data.

Usage:
    python tools/build_distribution.py
    python tools/build_distribution.py --output dist/
    python tools/build_distribution.py --include-models  # Include AI models (larger ZIP)
"""

import argparse
import os
import shutil
import zipfile
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Files/folders to ALWAYS exclude
EXCLUDE_PATTERNS = [
    # Virtual environments
    ".venv/",
    "venv/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    # Git
    ".git/",
    ".gitignore",
    ".gitattributes",
    # IDE
    ".vscode/",
    ".idea/",
    "*.code-workspace",
    # User data (regenerated per user)
    "index.faiss",
    "meta.sqlite",
    "logs/",
    "extracts/",
    "ai_search_docs/",
    # Build artifacts
    "dist/",
    "build/",
    "*.egg-info/",
    # Development files
    ".env",
    ".env.local",
    "*.log",
    "_TASK_STATUS.md",
    # Test artifacts
    ".pytest_cache/",
    "test_regression_results/",
    "benchmark_results/",
    ".coverage",
    "htmlcov/",
    # Backup files
    "backups/",
    "*.bak",
    # Cache
    ".cache/",
    "*.cache",
]

# Files/folders to exclude by default (but can be included with flags)
OPTIONAL_EXCLUDE = {
    "models": [
        "ai_models/",  # ~1.1GB - downloaded on first run via installer
    ],
}


def get_version() -> str:
    """Read version from VERSION file."""
    version_file = PROJECT_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "unknown"


def should_exclude(path: Path, exclude_patterns: list[str]) -> bool:
    """Check if a path should be excluded based on patterns."""
    path_str = str(path.relative_to(PROJECT_ROOT))

    for pattern in exclude_patterns:
        # Directory patterns (end with /)
        if pattern.endswith("/"):
            dir_pattern = pattern.rstrip("/")
            if path_str.startswith(dir_pattern) or f"/{dir_pattern}" in path_str:
                return True
            if path.is_dir() and path.name == dir_pattern:
                return True
        # Wildcard patterns
        elif pattern.startswith("*"):
            if path_str.endswith(pattern[1:]):
                return True
        # Exact matches
        else:
            if path_str == pattern or path.name == pattern:
                return True

    return False


def collect_files(
    include_models: bool = False,
) -> list[Path]:
    """Collect all files to include in the distribution."""
    exclude_patterns = EXCLUDE_PATTERNS.copy()

    if not include_models:
        exclude_patterns.extend(OPTIONAL_EXCLUDE["models"])

    files = []

    for item in PROJECT_ROOT.rglob("*"):
        if item.is_file():
            if not should_exclude(item, exclude_patterns):
                files.append(item)

    return files


def create_zip(
    output_dir: Path,
    include_models: bool = False,
) -> Path:
    """Create the distribution ZIP file."""
    version = get_version()

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine ZIP filename
    model_suffix = "-with-models" if include_models else ""
    zip_name = f"AI-File-Search-v{version}{model_suffix}.zip"
    zip_path = output_dir / zip_name

    # Remove existing ZIP if present
    if zip_path.exists():
        zip_path.unlink()

    # Collect files
    print(f"Collecting files for distribution...")
    files = collect_files(include_models=include_models)
    print(f"  Found {len(files)} files to include")

    # Create ZIP
    print(f"Creating {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            arcname = file_path.relative_to(PROJECT_ROOT)
            zf.write(file_path, f"ai-file-search/{arcname}")

    # Get size
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"  Size: {size_mb:.1f} MB")

    return zip_path


def create_version_file_for_cloud(output_dir: Path) -> Path:
    """Create a version.txt file for cloud hosting (update checking)."""
    version = get_version()
    version_file = output_dir / "latest_version.txt"
    version_file.write_text(version)
    print(
        f"Created {version_file.name} (upload this to Google Drive for update checking)"
    )
    return version_file


def main():
    parser = argparse.ArgumentParser(
        description="Build AI File Search distribution ZIP"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=PROJECT_ROOT / "dist",
        help="Output directory for ZIP file (default: dist/)",
    )
    parser.add_argument(
        "--include-models",
        action="store_true",
        help="Include AI models in ZIP (adds ~1.1GB)",
    )

    args = parser.parse_args()

    print("=" * 50)
    print("  AI File Search - Distribution Builder")
    print("=" * 50)
    print()

    # Create ZIP
    zip_path = create_zip(
        output_dir=args.output,
        include_models=args.include_models,
    )

    # Create version file for cloud
    version_file = create_version_file_for_cloud(args.output)

    print()
    print("=" * 50)
    print("  Build Complete!")
    print("=" * 50)
    print()
    print("Files created:")
    print(f"  1. {zip_path}")
    print(f"  2. {version_file}")
    print()
    print("Next steps:")
    print("  1. Upload ZIP to Google Drive")
    print("  2. Upload latest_version.txt to Google Drive")
    print("  3. Get shareable links and update core/version.py")
    print("  4. Share the ZIP link with your team")
    print()


if __name__ == "__main__":
    main()
