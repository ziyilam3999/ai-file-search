#!/usr/bin/env python3
"""
CLI Entry Point for AI File Search Watcher

This script provides a command-line interface for starting the file watcher daemon.
It supports configuration file override, dry-run mode for testing, and verbose output.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main_cli():
    """Main CLI entry point with argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AI File Search Watcher - Automatically index file changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_watcher.py                    # Start with default config
  python run_watcher.py --config my.yaml  # Use custom config file
  python run_watcher.py --dry-run         # Show config and exit
  python run_watcher.py --verbose         # Enable verbose logging
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="prompts/watcher_config.yaml",
        help="Path to configuration file (default: prompts/watcher_config.yaml)",
    )

    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Display configuration and exit without starting watcher",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging output"
    )

    args = parser.parse_args()

    # Import after path setup
    try:
        import yaml  # type: ignore

        from daemon.watch import FileWatcher
    except ImportError as e:
        print(f"Error importing required modules: {e}", file=sys.stderr)
        print("Make sure all dependencies are installed:", file=sys.stderr)
        print("  pip install watchdog apscheduler pyyaml loguru", file=sys.stderr)
        sys.exit(1)

    # Create watcher with specified config
    try:
        watcher = FileWatcher(config_path=args.config)
    except Exception as e:
        print(f"Error initializing watcher: {e}", file=sys.stderr)
        sys.exit(1)

    # Handle dry-run mode
    if args.dry_run:
        print("=== AI File Search Watcher Configuration ===")
        print(f"Config file: {args.config}")
        print(f"Config exists: {os.path.exists(args.config)}")
        print("\nConfiguration:")
        print(yaml.dump(watcher.config, default_flow_style=False, indent=2))

        # Show watch directories status
        print("\n=== Watch Directory Status ===")
        watch_dirs = watcher.config.get("watch_directories", [])
        for watch_dir in watch_dirs:
            exists = os.path.exists(watch_dir)
            print(f"  {watch_dir}: {'EXISTS' if exists else 'NOT FOUND'}")

        # Show file patterns
        print("\n=== File Patterns ===")
        patterns = watcher.config.get("file_patterns", {})
        include = patterns.get("include", [])
        ignore = patterns.get("ignore", [])
        print(f"  Include: {include}")
        print(f"  Ignore: {ignore}")

        return

    # Adjust logging level if verbose
    if args.verbose:
        if "logging" not in watcher.config:
            watcher.config["logging"] = {}
        watcher.config["logging"]["level"] = "DEBUG"
        watcher._setup_logging()  # Reconfigure logging

    # Start the watcher
    print("Starting AI File Search Watcher...")
    print(f"Using config: {args.config}")
    print("Press Ctrl+C to stop")

    try:
        watcher.run()
    except KeyboardInterrupt:
        print("\nWatcher stopped by user")
    except Exception as e:
        print(f"Error running watcher: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main_cli()
