#!/usr/bin/env python3
"""
Smart Watcher for AI File Search

Zero-configuration file watcher that automatically:
- Watches ALL folders in ai_search_docs/
- Detects new folders and starts watching them immediately
- Provides clear status feedback to users
- Enables easy start/stop/status operations

Usage:
    python smart_watcher.py start     # Start watching (background)
    python smart_watcher.py stop      # Stop watching
    python smart_watcher.py status    # Check if running
    python smart_watcher.py restart   # Stop and start again
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psutil


class SmartWatcherController:
    """Controls the smart watcher with easy start/stop/status operations."""

    def __init__(self):
        self.pid_file = Path("logs/watcher.pid")
        self.status_file = Path("logs/watcher_status.json")
        self.log_file = Path("logs/watcher.log")

        # Ensure logs directory exists
        self.log_file.parent.mkdir(exist_ok=True)

    def start_watcher(self, verbose: bool = False) -> bool:
        """Start the watcher in background mode."""
        if self.is_running():
            print("Watcher is already running!")
            self.show_status()
            return True

        print("Starting AI File Search Watcher...")

        # Ensure configuration is set to watch ALL folders
        self._setup_default_config()

        # Start the watcher process
        import subprocess

        cmd = [sys.executable, "run_watcher.py"]
        if verbose:
            cmd.append("--verbose")

        try:
            # Start process in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                ),
            )

            # Give it a moment to start
            time.sleep(2)

            # Check if it's actually running
            if process.poll() is None:  # Still running
                # Save PID
                with open(self.pid_file, "w") as f:
                    f.write(str(process.pid))

                # Save status
                self._update_status(
                    "running",
                    f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                )

                print("Watcher started successfully!")
                self._show_startup_info()
                return True
            else:
                print("Failed to start watcher")
                stdout, stderr = process.communicate()
                if stderr:
                    print(f"Error: {stderr.decode()}")
                return False

        except Exception as e:
            print(f"Error starting watcher: {e}")
            return False

    def stop_watcher(self) -> bool:
        """Stop the running watcher."""
        if not self.is_running():
            print("Watcher is not running")
            return True

        print("Stopping AI File Search Watcher...")

        try:
            pid = self._get_pid()
            if pid:
                # Try graceful shutdown first
                if os.name == "nt":  # Windows
                    import subprocess

                    result = subprocess.call(["taskkill", "/PID", str(pid), "/T", "/F"])
                    if result != 0:
                        print(f"Warning: taskkill returned {result}")
                else:  # Unix/Linux
                    os.kill(pid, signal.SIGTERM)

                # Wait for graceful shutdown
                time.sleep(2)

                # Force kill if still running
                if psutil.pid_exists(pid):
                    if os.name == "nt":
                        import subprocess

                        result = subprocess.call(
                            ["taskkill", "/PID", str(pid), "/T", "/F"]
                        )
                        if result != 0:
                            print(f"Warning: force taskkill returned {result}")
                    else:
                        os.kill(pid, signal.SIGTERM)

            # Clean up files
            self.pid_file.unlink(missing_ok=True)
            self._update_status(
                "stopped", f"Stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            print("Watcher stopped successfully!")
            return True

        except Exception as e:
            print(f"Error stopping watcher: {e}")
            return False

    def restart_watcher(self, verbose: bool = False) -> bool:
        """Restart the watcher and wait for initial scan."""
        print("Restarting AI File Search Watcher...")
        self.stop_watcher()
        time.sleep(1)
        success = self.start_watcher(verbose)

        if success:
            # Wait for initial scan to complete
            self._wait_for_scan_completion()

        return success

    def _wait_for_scan_completion(self, timeout: int = 30) -> bool:
        """Wait for watcher to complete initial scan."""
        print("Waiting for initial scan to complete...")
        start = time.time()

        while time.time() - start < timeout:
            status = self._get_status_info()
            if status and status.get("initial_scan_complete"):
                print("✓ Initial scan completed!")
                return True
            time.sleep(0.5)

        print("⚠ Warning: Initial scan taking longer than expected")
        return False

    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        pid = self._get_pid()
        return pid is not None and psutil.pid_exists(pid)

    def show_status(self) -> None:
        """Show detailed status information."""
        print("\nAI File Search Watcher Status:")
        print("=" * 50)

        if self.is_running():
            print("Status: RUNNING")

            # Show uptime
            pid = self._get_pid()
            if pid:
                try:
                    process = psutil.Process(pid)
                    start_time = datetime.fromtimestamp(process.create_time())
                    uptime = datetime.now() - start_time
                    print(f"Uptime: {self._format_duration(uptime)}")
                    print(f"PID: {pid}")
                except (ValueError, OSError):
                    pass
            # Show watched folders
            self._show_watched_folders()

            # Show recent activity
            self._show_recent_activity()

        else:
            print("Status: STOPPED")

            # Show last run info
            status_info = self._get_status_info()
            if status_info and "last_message" in status_info:
                print(f"Last activity: {status_info['last_message']}")

        print("\nCommands:")
        print("  python smart_watcher.py start    # Start watching")
        print("  python smart_watcher.py stop     # Stop watching")
        print("  python smart_watcher.py restart  # Restart watching")
        print("  python smart_watcher.py status   # Show this status")
        print()

    def _setup_default_config(self) -> bool:
        """Set up default configuration if needed."""
        # No longer enforcing Option 1 architecture or syncing categories
        # The watcher will load watch_paths from watcher_config.yaml
        return True

    def _get_pid(self) -> Optional[int]:
        """Get the PID of the running watcher."""
        try:
            if self.pid_file.exists():
                with open(self.pid_file, "r") as f:
                    return int(f.read().strip())
        except (ValueError, OSError):
            pass
        return None

    def _update_status(self, status: str, message: str) -> None:
        """Update the status file."""
        status_data = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "last_message": message,
        }

        with open(self.status_file, "w") as f:
            json.dump(status_data, f, indent=2)

    def _get_status_info(self) -> Optional[Dict]:
        """Get status information from file."""
        try:
            if self.status_file.exists():
                with open(self.status_file, "r") as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        return None

    def _show_startup_info(self) -> None:
        """Show helpful information after startup."""
        print("\nWhat's being watched:")
        self._show_watched_folders()

        print("\nHelpful tips:")
        print("  * Configure watched folders in the Settings UI")
        print("  * Check status anytime: python smart_watcher.py status")
        print("  * View logs: tail -f logs/watcher.log")
        print("  * Run app: python run_app.py")

    def _show_watched_folders(self) -> None:
        """Show which folders are being watched."""
        try:
            from core.config import load_watch_paths

            paths = load_watch_paths()
            if paths:
                print(f"Watched folders ({len(paths)}):")
                for p in paths:
                    print(f"  - {p}")
            else:
                print("Watched folders: None (Configure via Settings UI)")
        except Exception as e:
            print(f"Error loading watch paths: {e}")

    def _show_recent_activity(self) -> None:
        """Show recent log activity."""
        if self.log_file.exists():
            try:
                # Get last few lines of log
                with open(self.log_file, "r") as f:
                    lines = f.readlines()

                if lines:
                    print("Recent activity:")
                    for line in lines[-3:]:  # Last 3 lines
                        if line.strip():
                            print(f"  {line.strip()}")
            except (FileNotFoundError, OSError):
                pass

    def _format_duration(self, delta) -> str:
        """Format a timedelta as a human-readable string."""
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if not parts:  # Less than a minute
            parts.append(f"{seconds}s")

        return " ".join(parts)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Smart Watcher Controller for AI File Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python smart_watcher.py start           # Start watching all folders
  python smart_watcher.py start --verbose # Start with detailed logging
  python smart_watcher.py stop            # Stop the watcher
  python smart_watcher.py status          # Check current status
  python smart_watcher.py restart         # Stop and start again
        """,
    )

    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status"],
        help="Action to perform",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (for start/restart)",
    )

    args = parser.parse_args()

    controller = SmartWatcherController()

    if args.action == "start":
        success = controller.start_watcher(verbose=args.verbose)
        sys.exit(0 if success else 1)

    elif args.action == "stop":
        success = controller.stop_watcher()
        sys.exit(0 if success else 1)

    elif args.action == "restart":
        success = controller.restart_watcher(verbose=args.verbose)
        sys.exit(0 if success else 1)

    elif args.action == "status":
        controller.show_status()
        sys.exit(0)


if __name__ == "__main__":
    main()
