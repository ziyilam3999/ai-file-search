import json
import sys
import time
from pathlib import Path

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    stream_with_context,
)

# Add core modules to path
sys.path.append(str(Path(__file__).parent.parent))
from core.ask import answer_question
from core.index_manager import IndexManager
from core.monitoring import get_file_counts
from core.utils import format_citations, open_local_file
from smart_watcher import SmartWatcherController

app = Flask(__name__)
watcher = SmartWatcherController()
index_manager = IndexManager()


def to_activity(line: str) -> str | None:
    """Map log lines to user-friendly activity events.

    Args:
        line: A log line from app.log or watcher.log

    Returns:
        A user-friendly activity event string, or None if line is not a milestone
    """
    # Map known log lines to user-friendly milestones.
    if "PRELOAD: Pre-loading LLM model" in line:
        return "AI Model: Loading…"
    if "SUCCESS: LLM model loaded successfully" in line:
        return "AI Model: Loaded"
    if "PRELOAD: LLM model ready for queries" in line:
        return "AI Model: Ready"
    if "THINKING: Answering question:" in line:
        return "AI: Processing your question…"
    if "LOADING: FAISS index" in line:
        return "Search: Loading index…"
    if "SUCCESS: FAISS index loaded" in line:
        return "Search: Index ready"
    if "FOUND:" in line and "relevant chunks" in line:
        return line.split(" - ")[-1].strip()
    if "STREAMING: Starting generation" in line:
        return "AI: Generating answer…"
    if "FIRST TOKEN" in line:
        # Keep the timing info.
        return line.split(" - ")[-1].strip()
    if "TOTAL TIME" in line:
        return line.split(" - ")[-1].strip()

    # Watcher milestones (fallback)
    if "File watcher started successfully" in line:
        return "Watcher: Running"
    if "Processing" in line and "added/modified files" in line:
        return line.split(" - ")[-1].strip()
    if "Successfully added document:" in line:
        # Shorten a bit for UI.
        tail = line.split("Successfully added document:")[-1].strip()
        return f"Indexed: {tail}"
    if "Failed to add to index:" in line:
        tail = line.split("Failed to add to index:")[-1].strip()
        return f"Indexing failed: {tail}"

    return None


@app.route("/")
def home():
    # Check if this is first run (no config)
    try:
        from core.user_config import is_first_run

        if is_first_run():
            return redirect("/setup")
    except Exception:
        pass  # If check fails, show normal page
    return render_template("new_search.html")


@app.route("/setup")
def setup_wizard():
    """First-run setup wizard for new users."""
    return render_template("setup_wizard.html")


@app.route("/new-search")
def new_search():
    return render_template("new_search.html")


@app.route("/api/browse-folder", methods=["POST"])
def browse_folder():
    """Open native folder picker dialog via pywebview."""
    try:
        import webview

        # Get active window
        windows = webview.windows
        if not windows:
            return jsonify({"error": "No active window found"}), 400

        window = windows[0]

        # Open folder dialog
        result = window.create_file_dialog(
            webview.FOLDER_DIALOG, directory="", allow_multiple=False
        )

        if result and len(result) > 0:
            return jsonify({"path": result[0]})
        else:
            return jsonify({"path": None, "cancelled": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/open-file", methods=["POST"])
def api_open_file():
    """API endpoint to open a local file or Confluence page."""
    import webbrowser

    try:
        data = request.get_json()
        file_path = data.get("file_path")
        if not file_path:
            return jsonify({"error": "No file path provided"}), 400

        # Check if this is a Confluence path
        if file_path.startswith("confluence://"):
            from core.confluence import get_confluence_url_for_path

            confluence_url = get_confluence_url_for_path(file_path)
            if confluence_url:
                webbrowser.open(confluence_url)
                return jsonify(
                    {
                        "status": "success",
                        "message": f"Opened in browser: {confluence_url}",
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "error": "Could not resolve Confluence URL. Check your configuration."
                        }
                    ),
                    400,
                )
        else:
            open_local_file(file_path)
            return jsonify({"status": "success", "message": f"Opened {file_path}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/status")
def get_status():
    """Get system status for the UI status bar."""
    try:
        # Get watcher status
        is_running = watcher.is_running()

        # Get progress from watcher status file if available
        progress = {}
        try:
            status_file = Path("logs/watcher_status.json")
            if status_file.exists():
                with open(status_file, "r") as f:
                    status_data = json.load(f)
                    progress = status_data.get("progress", {})
        except Exception:
            pass

        # Get file counts
        (sample_count, extracts_count, indexed_count, _, _) = get_file_counts()

        # Check if AI model is loaded
        model_loaded = False
        try:
            from core.llm import _llm_instance

            model_loaded = _llm_instance is not None
        except Exception:
            pass

        return jsonify(
            {
                "watcher": "running" if is_running else "stopped",
                "documents": sample_count,
                "extracts": extracts_count,
                "indexed": indexed_count,
                "progress": progress,
                "model_loaded": model_loaded,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/preload-status")
def get_preload_status_endpoint():
    """Get AI model preload status."""
    try:
        # Try to import preload status from run_app
        import run_app

        status = run_app.get_preload_status()
        return jsonify(status)
    except Exception:
        # If not available, check if models are loaded directly
        from core.embedding import _MODEL_CACHE
        from core.llm import _llm_instance

        models_ready = _llm_instance is not None and _MODEL_CACHE is not None
        return jsonify(
            {
                "ready": models_ready,
                "stage": "Ready" if models_ready else "Loading...",
                "progress": 100 if models_ready else 50,
            }
        )


@app.route("/api/version")
def get_version_endpoint():
    """Get version info and update status."""
    try:
        from core.version import get_version_info

        return jsonify(get_version_info())
    except Exception as e:
        return jsonify({"version": "unknown", "error": str(e)})


@app.route("/api/logs")
def get_logs():
    """Get the last 80 lines of combined logs (app + watcher).

    This is intended for debugging; the UI should prefer `/api/activity`.
    """
    try:

        def read_tail(path: Path, limit: int) -> list[str]:
            if not path.exists():
                return []
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.readlines()[-limit:]
            except Exception as e:
                return [f"Error reading {path}: {e}\n"]

        app_lines = read_tail(Path("logs/app.log"), 80)
        watcher_lines = read_tail(Path("logs/watcher.log"), 80)
        lines = (app_lines + watcher_lines)[-80:]
        if not lines:
            return jsonify({"logs": ["No logs available yet.\n"]})

        return jsonify({"logs": lines})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/activity")
def get_activity():
    """Get user-meaningful activity events derived from logs.

    Returns a list of short, curated strings suitable for always-on UI display.
    """
    try:

        def read_tail(path: Path, limit: int) -> list[str]:
            if not path.exists():
                return []
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.readlines()[-limit:]

        # Prefer app runtime logs for meaningful milestones.
        lines = read_tail(Path("logs/app.log"), 250)
        if not lines:
            # Fall back to watcher log if app log isn't present yet.
            lines = read_tail(Path("logs/watcher.log"), 250)

        noise_substrings = [
            "GET /api/status",
            "GET /api/logs",
            "GET /api/activity",
            "GET /api/preload-status",
            "GET /static/",
            "GET /favicon.ico",
            "Ensured meta table exists",
            "WARNING: This is a development server",
        ]

        def is_noise(line: str) -> bool:
            return any(s in line for s in noise_substrings)

        events: list[str] = []

        for raw in lines:
            if is_noise(raw):
                continue
            event = to_activity(raw)
            if event:
                events.append(event)

        # Keep the most recent events, de-duplicated while preserving order.
        deduped: list[str] = []
        seen: set[str] = set()
        for event in reversed(events):
            if event in seen:
                continue
            seen.add(event)
            deduped.append(event)
            if len(deduped) >= 12:
                break
        deduped.reverse()

        if not deduped:
            deduped = ["Activity: Idle"]

        return jsonify({"events": deduped})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search", methods=["POST"])
def search():
    """Legacy non-streaming search endpoint."""
    try:
        data = request.json
        question = data.get("question", "")

        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Get answer from your existing core function
        # Use top_k=3 for faster response (reduced from 5)
        answer, citations = answer_question(question, top_k=3, streaming=False)

        # Format citations using shared utility
        formatted_citations = format_citations(citations)

        return jsonify(
            {
                "answer": answer,
                "citations": formatted_citations,
                "raw_citations": citations,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/stream", methods=["POST"])
def search_stream():
    """Streaming search endpoint using Server-Sent Events (SSE)."""
    data = request.json
    question = data.get("question", "")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    def generate():
        try:
            # Call core function with streaming=True
            # Returns tuple: (generator, citations_list)
            # Use top_k=3 for faster response (reduced from 5)
            answer_generator, citations = answer_question(
                question, top_k=3, streaming=True
            )

            # 1. Stream the answer tokens
            for token in answer_generator:
                if token:
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # 2. Send structured citations at the end
            formatted = format_citations(citations)
            yield f"data: {json.dumps({'type': 'citations', 'content': formatted})}\n\n"

            # 3. Signal completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx/proxy buffering
            "Connection": "keep-alive",
        },
    )


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/api/settings/watch-paths", methods=["GET"])
def get_watch_paths():
    paths = index_manager.get_watch_paths()
    return jsonify({"paths": paths})


@app.route("/api/settings/watch-paths", methods=["POST"])
def add_watch_path():
    data = request.json
    path = data.get("path")
    if not path:
        return jsonify({"error": "Path is required"}), 400

    # Use async mode by default for faster response
    async_mode = data.get("async", True)
    success, message, job_id = index_manager.add_watch_path(path, async_mode=async_mode)

    if success:
        response = {
            "status": "accepted" if job_id else "success",
            "message": message,
        }
        if job_id:
            response["job_id"] = job_id
            response["poll_url"] = f"/api/jobs/{job_id}"
        return jsonify(response)
    else:
        return jsonify({"error": message}), 400


@app.route("/api/settings/watch-paths", methods=["DELETE"])
def remove_watch_path():
    data = request.json
    path = data.get("path")
    if not path:
        return jsonify({"error": "Path is required"}), 400

    # Use async mode by default for faster response
    async_mode = data.get("async", True)
    success, message, job_id = index_manager.remove_watch_path(
        path, async_mode=async_mode
    )

    if success:
        response = {
            "status": "accepted" if job_id else "success",
            "message": message,
        }
        if job_id:
            response["job_id"] = job_id
            response["poll_url"] = f"/api/jobs/{job_id}"
        return jsonify(response)
    else:
        return jsonify({"error": message}), 400


@app.route("/api/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """Get the status of a background job."""
    job = index_manager.get_job_status(job_id)
    if job:
        return jsonify(job)
    else:
        return jsonify({"error": "Job not found"}), 404


@app.route("/api/jobs", methods=["GET"])
def list_jobs():
    """List all background jobs."""
    jobs = index_manager.get_all_jobs()
    return jsonify({"jobs": jobs})


@app.route("/api/settings/reindex", methods=["POST"])
def trigger_reindex():
    success, message = index_manager.trigger_reindex()
    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"error": message}), 500


# =============================================================================
# Confluence Integration API
# =============================================================================


@app.route("/api/confluence/status", methods=["GET"])
def get_confluence_status():
    """Get Confluence connection and sync status."""
    try:
        status = index_manager.get_confluence_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/confluence/test", methods=["POST"])
def test_confluence_connection():
    """Test Confluence connection with current credentials."""
    try:
        success, message = index_manager.test_confluence_connection()
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/confluence/spaces", methods=["GET"])
def get_confluence_spaces():
    """Get list of accessible Confluence spaces."""
    try:
        spaces = index_manager.get_confluence_spaces()
        return jsonify({"spaces": spaces})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/confluence/sync", methods=["POST"])
def sync_confluence():
    """Start Confluence sync for a space."""
    try:
        data = request.json or {}
        space_key = data.get("space_key")

        if not space_key:
            return jsonify({"error": "space_key is required"}), 400

        incremental = data.get("incremental", True)
        async_mode = data.get("async", True)

        success, message, job_id = index_manager.sync_confluence(
            space_key=space_key,
            async_mode=async_mode,
            incremental=incremental,
        )

        if success:
            response = {
                "status": "accepted" if job_id else "success",
                "message": message,
            }
            if job_id:
                response["job_id"] = job_id
                response["poll_url"] = f"/api/jobs/{job_id}"
            return jsonify(response)
        else:
            return jsonify({"error": message}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# USER CONFIG API ENDPOINTS
# =============================================================================


@app.route("/api/user-config", methods=["GET"])
def get_user_config():
    """Get user configuration (non-sensitive settings only)."""
    try:
        from core.user_config import get_confluence_config, is_first_run

        return jsonify(
            {
                "is_first_run": is_first_run(),
                "confluence": get_confluence_config(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/user-config/confluence", methods=["POST"])
def save_confluence_settings():
    """Save Confluence configuration (credentials + settings)."""
    try:
        from core.user_config import save_confluence_config

        data = request.json or {}

        # Extract fields (all optional - only provided fields are updated)
        url = data.get("url")
        email = data.get("email")
        token = data.get("token")
        default_space = data.get("default_space")
        visible_spaces = data.get("visible_spaces")

        success = save_confluence_config(
            url=url,
            email=email,
            token=token,
            default_space=default_space,
            visible_spaces=visible_spaces,
        )

        if success:
            return jsonify({"status": "saved", "message": "Confluence settings saved"})
        else:
            return jsonify({"error": "Failed to save settings"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/user-config/confluence/test", methods=["POST"])
def test_new_confluence_connection():
    """Test Confluence connection with provided credentials."""
    try:
        data = request.json or {}
        url = data.get("url", "").strip()
        email = data.get("email", "").strip()
        token = data.get("token", "").strip()

        if not all([url, email, token]):
            return jsonify({"error": "URL, email, and token are required"}), 400

        # Try to connect with provided credentials
        from atlassian import Confluence

        client = Confluence(
            url=url,
            username=email,
            password=token,
            cloud=True,
        )

        # Try to get spaces as a connection test
        client.get_all_spaces(limit=1)

        return jsonify(
            {
                "status": "success",
                "message": f"Connected to {url}",
            }
        )

    except Exception as e:
        return jsonify({"error": f"Connection failed: {str(e)}"}), 400


@app.route("/api/user-config/default-space", methods=["POST"])
def set_default_space():
    """Set the default Confluence space."""
    try:
        from core.user_config import set_setting

        data = request.json or {}
        space_key = data.get("space_key")
        space_name = data.get("space_name", "")

        if not space_key:
            return jsonify({"error": "space_key is required"}), 400

        set_setting("default_space", space_key)

        return jsonify(
            {
                "status": "saved",
                "message": f"Default space set to {space_name or space_key}",
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Pre-warm the embedding adapter at startup for faster first requests
@app.before_request
def warm_up_once():
    """Warm up the embedding adapter on first request and sync missing files."""
    if not getattr(app, "_warmed_up", False):
        try:
            index_manager.warm_up()
            # Check for files that weren't indexed (e.g., app closed during indexing)
            # Run in background thread so it doesn't block the window from opening
            import threading

            sync_thread = threading.Thread(
                target=index_manager.startup_sync_check,
                daemon=True,
                name="StartupSyncCheck",
            )
            sync_thread.start()
            app._warmed_up = True
        except Exception:
            pass  # Ignore warm-up errors


if __name__ == "__main__":
    app.run(debug=True, port=5001)
