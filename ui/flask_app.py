import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

# Add core modules to path
sys.path.append(str(Path(__file__).parent.parent))
from core.ask import answer_question

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("new_search.html")


@app.route("/new-search")
def new_search():
    return render_template("new_search.html")


@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.json
        question = data.get("question", "")

        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Get answer from your existing core function
        answer, citations = answer_question(question, streaming=False)

        return jsonify({"answer": answer, "citations": citations})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Different port from Streamlit
