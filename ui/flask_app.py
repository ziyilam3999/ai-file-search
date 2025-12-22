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

        # Get file counts
        (sample_count, extracts_count, indexed_count, _, _) = get_file_counts()

        return jsonify(
            {
                "watcher": "running" if is_running else "stopped",
                "documents": sample_count,
                "extracts": extracts_count,
                "indexed": indexed_count,
            }
        )
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

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


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
