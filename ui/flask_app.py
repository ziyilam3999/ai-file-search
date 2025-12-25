import json
import sys
import time
from pathlib import Path

from flask import (
    Flask,
    Response,
    jsonify,
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


@app.route("/")
def home():
    return render_template("new_search.html")


@app.route("/new-search")
def new_search():
    return render_template("new_search.html")


@app.route("/api/open-file", methods=["POST"])
def api_open_file():
    """API endpoint to open a local file."""
    try:
        data = request.get_json()
        file_path = data.get("file_path")
        if not file_path:
            return jsonify({"error": "No file path provided"}), 400

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
            from core.llm import _phi3_instance

            model_loaded = _phi3_instance is not None
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
        from core.llm import _phi3_instance

        models_ready = _phi3_instance is not None and _MODEL_CACHE is not None
        return jsonify(
            {
                "ready": models_ready,
                "stage": "Ready" if models_ready else "Loading...",
                "progress": 100 if models_ready else 50,
            }
        )


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
            "GET /static/",
            "GET /favicon.ico",
            "Ensured meta table exists",
            "WARNING: This is a development server",
        ]

        def is_noise(line: str) -> bool:
            return any(s in line for s in noise_substrings)

        def to_activity(line: str) -> str | None:
            # Map known log lines to user-friendly milestones.
            if "PRELOAD: Pre-loading Phi-3 model" in line:
                return "AI Model: Loading…"
            if "SUCCESS: Phi-3 model loaded successfully" in line:
                return "AI Model: Loaded"
            if "PRELOAD: Phi-3 model ready for queries" in line:
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
        # Use top_k=5 to ensure we get enough context
        answer, citations = answer_question(question, top_k=5, streaming=False)

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
            # Use top_k=5 to ensure we get enough context
            answer_generator, citations = answer_question(
                question, top_k=5, streaming=True
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

    success, message = index_manager.add_watch_path(path)
    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/settings/watch-paths", methods=["DELETE"])
def remove_watch_path():
    data = request.json
    path = data.get("path")
    if not path:
        return jsonify({"error": "Path is required"}), 400

    success, message = index_manager.remove_watch_path(path)
    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"error": message}), 400


@app.route("/api/settings/reindex", methods=["POST"])
def trigger_reindex():
    success, message = index_manager.trigger_reindex()
    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"error": message}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
