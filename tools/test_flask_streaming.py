"""Diagnostic: Test Flask streaming endpoint directly using raw sockets.

This script tests the /search/stream endpoint with raw socket connection
to avoid buffering issues in the requests library.
"""

import json
import socket
import time


def test_flask_streaming():
    """Test the Flask /search/stream endpoint using raw sockets."""
    print("=" * 60)
    print("FLASK SSE STREAMING DIAGNOSTIC (Raw Socket)")
    print("=" * 60)

    # Check if Flask is running
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(("127.0.0.1", 5001))
        sock.close()
        print("✓ Flask server is running on port 5001")
    except (socket.error, socket.timeout):
        print("✗ Flask server is NOT running!")
        print("  Please start the app first: poetry run python run_app.py")
        return

    question = "What is machine learning?"

    print(f"\nTest question: '{question}'")
    print("-" * 60)

    # Build HTTP request
    body = json.dumps({"question": question})
    request = (
        f"POST /search/stream HTTP/1.1\r\n"
        f"Host: localhost:5001\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: keep-alive\r\n"
        f"\r\n"
        f"{body}"
    )

    start_time = time.perf_counter()
    first_byte_time = None
    first_token_time = None
    token_count = 0
    full_answer = ""

    print("\nStreaming tokens:")
    print("-" * 40)

    try:
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 5001))
        sock.settimeout(30)

        # Send request
        sock.sendall(request.encode())

        # Read response
        buffer = b""
        in_body = False

        while True:
            chunk = sock.recv(4096)
            now = time.perf_counter()

            if not chunk:
                break

            if first_byte_time is None:
                first_byte_time = now

            buffer += chunk
            text = buffer.decode("utf-8", errors="ignore")

            # Skip HTTP headers
            if not in_body:
                if "\r\n\r\n" in text:
                    in_body = True
                    text = text.split("\r\n\r\n", 1)[1]
                else:
                    continue

            # Parse SSE events
            lines = text.split("\n")
            for line in lines:
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])

                        if data.get("type") == "token":
                            token = data.get("content", "")
                            if token:
                                token_count += 1
                                if first_token_time is None:
                                    first_token_time = now
                                    ttft = first_token_time - start_time
                                    print(f"\n[FIRST TOKEN at {ttft*1000:.0f}ms]")
                                full_answer += token
                                print(token, end="", flush=True)

                        elif data.get("type") == "citations":
                            print("\n\n[Citations received]")

                        elif data.get("type") == "done":
                            print("\n[Stream complete]")
                            sock.close()
                            break

                        elif data.get("type") == "error":
                            print(f"\n[ERROR: {data.get('content')}]")

                    except json.JSONDecodeError:
                        pass

    except Exception as e:
        print(f"\n✗ Request error: {e}")
        return
    finally:
        try:
            sock.close()
        except Exception:
            pass

    total_time = time.perf_counter() - start_time

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    if first_token_time:
        print(f"First token:   {(first_token_time - start_time)*1000:.0f}ms")
    else:
        print("First token:   No tokens received")
    print(f"Total time:    {total_time*1000:.0f}ms")
    print(f"Tokens:        {token_count}")
    print(f"Answer length: {len(full_answer)} chars")

    # Performance evaluation
    print("\n" + "-" * 60)
    print("PERFORMANCE EVALUATION")
    print("-" * 60)
    if first_token_time:
        ttft_ms = (first_token_time - start_time) * 1000
        if ttft_ms < 250:
            print(f"✓ Excellent: {ttft_ms:.0f}ms to first token")
        elif ttft_ms < 500:
            print(f"✓ Good: {ttft_ms:.0f}ms to first token")
        elif ttft_ms < 1000:
            print(f"⚠ Acceptable: {ttft_ms:.0f}ms to first token")
        else:
            print(f"⚠ Slow: {ttft_ms:.0f}ms to first token (target: <500ms)")


if __name__ == "__main__":
    test_flask_streaming()
