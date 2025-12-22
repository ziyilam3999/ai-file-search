import os
import sys
import threading
import time

import requests
import webview

from smart_watcher import SmartWatcherController


def preload_model():
    """Pre-load the Phi-3 model in the background."""
    try:
        from core.llm import preload_phi3_llm

        preload_phi3_llm()
    except Exception as e:
        print(f"Launcher: Model pre-load failed (will load on first query): {e}")


def start_flask():
    """Starts the Flask server in a background thread."""
    # Import here to avoid circular imports or side effects
    from ui.flask_app import app

    # Run without debug mode for production-like behavior
    app.run(port=5001, use_reloader=False)


def ensure_watcher_running():
    """Checks if the file watcher is running and starts it if not."""
    watcher = SmartWatcherController()
    if not watcher.is_running():
        print("Launcher: Starting file watcher...")
        watcher.start_watcher()
    else:
        print("Launcher: File watcher is already running.")


def wait_for_server(port=5001, timeout=10):
    """Waits for the Flask server to be ready."""
    start_time = time.time()
    url = f"http://localhost:{port}/"
    while time.time() - start_time < timeout:
        try:
            requests.get(url)
            return True
        except requests.ConnectionError:
            time.sleep(0.5)
    return False


def start_app():
    print("Launcher: Initializing AI File Search...")

    # 1. Ensure Watcher is running
    ensure_watcher_running()

    # 2. Pre-load AI model in background to avoid cold start on first query
    print("Launcher: Pre-loading AI model...")
    preload_thread = threading.Thread(target=preload_model, daemon=True)
    preload_thread.start()

    # 3. Start Flask in a separate thread
    print("Launcher: Starting UI server...")
    server_thread = threading.Thread(target=start_flask, daemon=True)
    server_thread.start()

    # 4. Wait for server to initialize
    if wait_for_server():
        print("Launcher: Server ready. Opening window...")

        # 4. Create the native window
        webview.create_window(
            "AI File Search",
            "http://localhost:5001",
            width=1200,
            height=800,
            min_size=(800, 600),
            text_select=True,
        )

        # 5. Start the webview GUI loop
        webview.start()
    else:
        print("Launcher: Failed to start UI server.")
        sys.exit(1)


if __name__ == "__main__":
    start_app()
