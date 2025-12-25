"""Precise timing diagnostic using raw sockets to identify exact bottlenecks.

Measures each phase of the streaming request lifecycle.
"""

import json
import socket
import time


def test_timing_breakdown():
    """Measure precise timing of Flask streaming request phases."""
    print("=" * 60)
    print("PRECISE TIMING BREAKDOWN (Raw Socket)")
    print("=" * 60)

    # Check server
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(("127.0.0.1", 5001))
        sock.close()
        print("✓ Flask server is running on port 5001\n")
    except (socket.error, socket.timeout):
        print("✗ Flask server not running. Start with: poetry run python run_app.py")
        return

    question = "What is machine learning?"
    print(f"Question: '{question}'")
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

    t0 = time.perf_counter()

    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 5001))
    sock.settimeout(30)

    t_connected = time.perf_counter()
    print(f"\n[1] Socket connected: {(t_connected - t0)*1000:.0f}ms")

    # Send request
    sock.sendall(request.encode())
    t_sent = time.perf_counter()
    print(f"[2] Request sent: {(t_sent - t0)*1000:.0f}ms")

    # Read response
    buffer = b""
    in_body = False
    first_byte_time = None
    first_token_time = None
    token_count = 0

    while True:
        try:
            chunk = sock.recv(4096)
            now = time.perf_counter()

            if not chunk:
                break

            if first_byte_time is None:
                first_byte_time = now
                print(f"[3] First byte (TTFB): {(first_byte_time - t0)*1000:.0f}ms")

            buffer += chunk
            text = buffer.decode("utf-8", errors="ignore")

            # Skip HTTP headers
            if not in_body:
                if "\r\n\r\n" in text:
                    in_body = True
                    text = text.split("\r\n\r\n", 1)[1]
                else:
                    continue

            # Parse SSE
            for line in text.split("\n"):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])

                        if data.get("type") == "token" and data.get("content"):
                            token_count += 1
                            if first_token_time is None:
                                first_token_time = now
                                print(
                                    f"[4] First TOKEN: {(first_token_time - t0)*1000:.0f}ms"
                                )

                        if data.get("type") == "done":
                            sock.close()
                            t_end = time.perf_counter()
                            print(
                                f"[5] Complete: {(t_end - t0)*1000:.0f}ms (tokens: {token_count})"
                            )

                            # Breakdown
                            print("\n" + "=" * 60)
                            print("TIMING BREAKDOWN")
                            print("=" * 60)

                            conn_ms = (t_connected - t0) * 1000
                            ttfb_ms = (
                                (first_byte_time - t0) * 1000 if first_byte_time else 0
                            )
                            ttft_ms = (
                                (first_token_time - t0) * 1000
                                if first_token_time
                                else 0
                            )
                            stream_ms = (
                                (t_end - first_token_time) * 1000
                                if first_token_time
                                else 0
                            )

                            print(f"{'Phase':<35} {'Time':<12} {'Cumulative':<12}")
                            print("-" * 60)
                            print(
                                f"{'TCP Connection':<35} {conn_ms:>8.0f}ms {conn_ms:>10.0f}ms"
                            )
                            print(
                                f"{'Server Processing (to TTFB)':<35} {(ttfb_ms - conn_ms):>8.0f}ms {ttfb_ms:>10.0f}ms"
                            )
                            print(
                                f"{'LLM First Token':<35} {(ttft_ms - ttfb_ms):>8.0f}ms {ttft_ms:>10.0f}ms"
                            )
                            print(
                                f"{'Remaining Stream':<35} {stream_ms:>8.0f}ms {(t_end - t0)*1000:>10.0f}ms"
                            )

                            # Analysis
                            print("\n" + "=" * 60)
                            print("PERFORMANCE ANALYSIS")
                            print("=" * 60)

                            if ttft_ms < 250:
                                print(f"✓ Excellent: {ttft_ms:.0f}ms to first token")
                            elif ttft_ms < 500:
                                print(f"✓ Good: {ttft_ms:.0f}ms to first token")
                            elif ttft_ms < 1000:
                                print(f"⚠ Acceptable: {ttft_ms:.0f}ms to first token")
                            else:
                                print(f"⚠ Slow: {ttft_ms:.0f}ms - optimization needed")

                                # Identify bottlenecks
                                if (ttfb_ms - conn_ms) > 500:
                                    print(
                                        f"   → Server processing is slow: {(ttfb_ms - conn_ms):.0f}ms"
                                    )
                                if (ttft_ms - ttfb_ms) > 200:
                                    print(
                                        f"   → LLM generation is slow: {(ttft_ms - ttfb_ms):.0f}ms"
                                    )

                            return

                    except json.JSONDecodeError:
                        pass

        except socket.timeout:
            print("Socket timeout")
            break

    sock.close()


if __name__ == "__main__":
    test_timing_breakdown()
