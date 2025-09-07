#!/usr/bin/env python3
"""
File Watcher Monitor

Real-time monitoring tool for the file watcher system.
Tracks file processing events and provides live updates.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path


class WatcherMonitor:
    """Monitor file watcher activity in real-time."""

    def __init__(self):
        self.log_file = Path("logs/watcher.log")
        self.status_file = Path("logs/watcher_status.json")
        self.last_position = 0

    def check_watcher_status(self):
        """Check if watcher is running."""
        try:
            if self.status_file.exists():
                with open(self.status_file, "r") as f:
                    status = json.load(f)
                    return status.get("status") == "running"
        except Exception:  # Fixed: was bare 'except'
            pass
        return False

    def get_latest_log_entries(self, lines=10):
        """Get the latest log entries."""
        if not self.log_file.exists():
            return []

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if all_lines else []
        except Exception as e:
            print(f"Error reading log file: {e}")
            return []

    def monitor_live_changes(self, duration=60):
        """Monitor file changes in real-time for specified duration."""
        print(f"🔍 STARTING LIVE MONITORING")
        print(f"Duration: {duration} seconds")
        print(f"Log file: {self.log_file}")
        print(f"{'='*60}")

        if not self.check_watcher_status():
            print("⚠️  Warning: Watcher may not be running")
            print("Start with: python smart_watcher.py start")
            print()

        start_time = time.time()
        last_size = self.log_file.stat().st_size if self.log_file.exists() else 0

        print("📊 Monitoring started - waiting for file changes...")
        print("Press Ctrl+C to stop early\n")

        try:
            while time.time() - start_time < duration:
                if self.log_file.exists():
                    current_size = self.log_file.stat().st_size

                    if current_size > last_size:
                        # New content added
                        with open(self.log_file, "r", encoding="utf-8") as f:
                            f.seek(last_size)
                            new_lines = f.read().splitlines()

                        for line in new_lines:
                            if any(
                                keyword in line.lower()
                                for keyword in [
                                    "processing",
                                    "added",
                                    "updated",
                                    "deleted",
                                    "error",
                                    "success",
                                ]
                            ):
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                print(f"[{timestamp}] {line.strip()}")

                        last_size = current_size

                time.sleep(1)

        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")

        elapsed = time.time() - start_time
        print(f"\n📊 Monitoring completed ({elapsed:.1f} seconds)")

    def show_recent_activity(self, lines=20):
        """Show recent watcher activity."""
        print(f"📋 RECENT WATCHER ACTIVITY (last {lines} lines)")
        print(f"{'='*60}")

        recent_lines = self.get_latest_log_entries(lines)

        if not recent_lines:
            print("❌ No log entries found")
            return

        for line in recent_lines:
            line = line.strip()
            if line:
                # Highlight important events
                if "ERROR" in line:
                    print(f"❌ {line}")
                elif "SUCCESS" in line or "added document" in line:
                    print(f"✅ {line}")
                elif "processing" in line.lower():
                    print(f"⚙️  {line}")
                else:
                    print(f"ℹ️  {line}")

        print(f"{'='*60}")


def main():
    """Main function with command line options."""
    monitor = WatcherMonitor()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "status":
            is_running = monitor.check_watcher_status()
            print(f"🔍 Watcher Status: {'🟢 RUNNING' if is_running else '🔴 STOPPED'}")

        elif command == "recent":
            lines = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            monitor.show_recent_activity(lines)

        elif command == "live":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            monitor.monitor_live_changes(duration)

        else:
            print("❌ Unknown command")
            print_usage()
    else:
        print_usage()


def print_usage():
    """Print usage information."""
    print(
        """
🔍 File Watcher Monitor

USAGE:
    python tools/monitor_watcher.py <command> [options]

COMMANDS:
    status              Check if watcher is running
    recent [lines]      Show recent log entries (default: 20 lines)
    live [seconds]      Monitor live changes (default: 60 seconds)

EXAMPLES:
    python tools/monitor_watcher.py status
    python tools/monitor_watcher.py recent 50
    python tools/monitor_watcher.py live 120
    """
    )


if __name__ == "__main__":
    main()
