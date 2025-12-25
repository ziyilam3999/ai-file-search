import os
import sys
import threading
import time

import requests
import webview

from smart_watcher import SmartWatcherController


def configure_app_logging() -> None:
    """Configure Loguru to also write app runtime logs to logs/app.log."""
    try:
        from loguru import logger

        os.makedirs("logs", exist_ok=True)

        # Avoid duplicate sinks if run_app is restarted in the same interpreter.
        logger.add(
            "logs/app.log",
            rotation="5 MB",
            retention=10,
            enqueue=True,
            backtrace=False,
            diagnose=False,
        )
    except Exception as e:
        print(f"Launcher: Logging configuration failed: {e}")


def preload_models():
    """Pre-load AI models (LLM + embeddings) in the background.

    This eliminates cold-start delays on the first query by loading:
    1. Phi-3.5 LLM (~3s cold load)
    2. Sentence transformer embedding model (~4s cold load)
    3. FAISS index and metadata cache (~1s cold load)
    """
    try:
        # 1. Pre-load embedding model and caches
        print("Launcher: Pre-loading embedding model...")
        from core.embedding import Embedder

        embedder = Embedder()
        embedder._get_model()  # Load sentence transformer
        embedder._get_index()  # Load FAISS index
        embedder._get_metadata()  # Load metadata cache
        print("Launcher: Embedding model ready.")

        # 2. Pre-load Phi-3 LLM
        print("Launcher: Pre-loading Phi-3 LLM...")
        from core.llm import preload_phi3_llm

        preload_phi3_llm()
        print("Launcher: All AI models ready for queries!")

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

    # Configure app logging before starting threads.
    configure_app_logging()

    # 1. Ensure Watcher is running
    ensure_watcher_running()

    # 2. Start Flask in a separate thread FIRST
    print("Launcher: Starting UI server...")
    server_thread = threading.Thread(target=start_flask, daemon=True)
    server_thread.start()

    # 3. Wait for server to initialize
    if wait_for_server():
        print("Launcher: Server ready. Opening window...")

        # 4. Pre-load AI models in background AFTER Flask is ready
        print("Launcher: Pre-loading AI models in background...")
        preload_thread = threading.Thread(target=preload_models, daemon=True)
        preload_thread.start()

        # 5. Create the native window
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
