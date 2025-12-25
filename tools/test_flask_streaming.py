"""Diagnostic: Test Flask streaming endpoint directly.

This script diagnoses why Flask SSE streaming takes 70+ seconds
while isolated streaming takes only 4 seconds.
"""

import json
import sys
import time

import requests


def test_flask_streaming():
    """Test the Flask /search/stream endpoint directly."""
    print("=" * 60)
    print("FLASK SSE STREAMING DIAGNOSTIC")
    print("=" * 60)

    # Check if Flask is running
    try:
        requests.get("http://localhost:5001/", timeout=2)
        print("✓ Flask server is running on port 5001")
    except requests.exceptions.ConnectionError:
        print("✗ Flask server is NOT running!")
        print("  Please start the app first: poetry run python run_app.py")
        return

    question = "What is machine learning?"

    print(f"\nTest question: '{question}'")
    print("-" * 60)

    start_time = time.time()
    first_token_time = None
    token_count = 0
    full_answer = ""

    print("\nStreaming tokens:")
    print("-" * 40)

    try:
        # Make streaming request
        response = requests.post(
            "http://localhost:5001/search/stream",
            json={"question": question},
            stream=True,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code != 200:
            print(f"✗ HTTP Error: {response.status_code}")
            return

        # Parse SSE stream
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])  # Skip "data: " prefix

                    if data.get("type") == "token":
                        token = data.get("content", "")
                        if token:
                            token_count += 1
                            if first_token_time is None:
                                first_token_time = time.time()
                                ttft = first_token_time - start_time
                                print(f"\n[FIRST TOKEN at {ttft:.2f}s]")
                            full_answer += token
                            print(token, end="", flush=True)

                    elif data.get("type") == "citations":
                        print("\n\n[Citations received]")

                    elif data.get("type") == "done":
                        print("\n[Stream complete]")

                    elif data.get("type") == "error":
                        print(f"\n[ERROR: {data.get('content')}]")

                except json.JSONDecodeError as e:
                    print(f"\n[Parse error: {e}]")

    except Exception as e:
        print(f"\n✗ Request error: {e}")
        return

    total_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(
        f"First token:   {first_token_time - start_time:.2f}s"
        if first_token_time
        else "No tokens received"
    )
    print(f"Total time:    {total_time:.2f}s")
    print(f"Tokens:        {token_count}")
    print(f"Answer length: {len(full_answer)} chars")

    # Comparison
    print("\n" + "-" * 60)
    print("COMPARISON (Flask vs Isolated)")
    print("-" * 60)
    print(f"{'Metric':<20} {'Flask':<15} {'Isolated':<15}")
    print(
        f"{'First token':<20} {f'{first_token_time - start_time:.2f}s' if first_token_time else 'N/A':<15} {'0.75s':<15}"
    )
    print(f"{'Total time':<20} {f'{total_time:.2f}s':<15} {'4.07s':<15}")

    if first_token_time and (first_token_time - start_time) > 10:
        print("\n⚠️  ISSUE DETECTED: Flask streaming is significantly slower!")
        print("   Possible causes:")
        print("   1. Flask development server buffering")
        print("   2. Model loading on every request")
        print("   3. Embedder/retrieval taking too long")
        print("   4. Response buffering in Flask/Werkzeug")


if __name__ == "__main__":
    test_flask_streaming()
