"""Test to verify if the issue is Flask buffering or requests library buffering."""

import json
import socket
import time


def test_raw_socket():
    """Bypass requests library - use raw sockets to test Flask directly."""
    print("=" * 60)
    print("RAW SOCKET TEST (bypassing requests library)")
    print("=" * 60)

    question = "What is machine learning?"

    # Build HTTP request manually
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

    # Create socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 5001))
    sock.settimeout(30)

    t_connected = time.perf_counter()
    print(f"[1] Socket connected: {(t_connected - t0)*1000:.0f}ms")

    # Send request
    sock.sendall(request.encode())
    t_sent = time.perf_counter()
    print(f"[2] Request sent: {(t_sent - t0)*1000:.0f}ms")

    # Read response in chunks
    first_byte_time = None
    first_data_time = None
    buffer = b""
    token_count = 0

    while True:
        try:
            chunk = sock.recv(4096)
            now = time.perf_counter()

            if not chunk:
                break

            if first_byte_time is None:
                first_byte_time = now
                print(f"[3] First byte received: {(first_byte_time - t0)*1000:.0f}ms")

            buffer += chunk
            text = buffer.decode("utf-8", errors="ignore")

            # Look for SSE data lines
            for line in text.split("\n"):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "token" and data.get("content"):
                            token_count += 1
                            if first_data_time is None:
                                first_data_time = now
                                print(
                                    f"[4] First TOKEN: {(first_data_time - t0)*1000:.0f}ms"
                                )
                        if data.get("type") == "done":
                            sock.close()
                            t_end = time.perf_counter()
                            print(
                                f"[5] Complete: {(t_end - t0)*1000:.0f}ms (tokens: {token_count})"
                            )
                            return
                    except json.JSONDecodeError:
                        pass

        except socket.timeout:
            print("Socket timeout")
            break

    sock.close()


if __name__ == "__main__":
    test_raw_socket()
