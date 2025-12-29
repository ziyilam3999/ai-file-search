"""Download Qwen2.5-1.5B model with resume capability."""

import os
import sys
from pathlib import Path

import requests

URL = "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
OUTPUT_FILE = Path("ai_models/qwen2.5-1.5b-instruct-q4_k_m.gguf")
EXPECTED_SIZE = 1091091459  # bytes (1.041 GB)


def download_with_progress(url, output_path, expected_size):
    """Download file with progress bar and resume capability."""

    # Check if partial file exists
    start_byte = 0
    if output_path.exists():
        start_byte = output_path.stat().st_size
        if start_byte == expected_size:
            print(f"✓ File already downloaded: {output_path.name}")
            return True
        elif start_byte > 0:
            print(
                f"Resuming download from {start_byte:,} bytes ({start_byte / expected_size * 100:.1f}%)"
            )

    # Setup headers for resume
    headers = {}
    if start_byte > 0:
        headers["Range"] = f"bytes={start_byte}-"

    try:
        # Stream download
        mode = "ab" if start_byte > 0 else "wb"
        with requests.get(url, headers=headers, stream=True, timeout=30) as response:
            response.raise_for_status()

            # Get total size
            content_length = response.headers.get("Content-Length")
            if content_length:
                total_size = int(content_length) + start_byte
            else:
                total_size = expected_size

            print(f"Downloading: {output_path.name}")
            print(
                f"Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.1f} MB)"
            )

            # Download with progress
            downloaded = start_byte
            with open(output_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Print progress every 10MB
                        if downloaded % (10 * 1024 * 1024) < 8192:
                            percent = downloaded / total_size * 100
                            mb_downloaded = downloaded / 1024 / 1024
                            mb_total = total_size / 1024 / 1024
                            print(
                                f"Progress: {mb_downloaded:.1f} / {mb_total:.1f} MB ({percent:.1f}%)"
                            )

            # Verify size
            final_size = output_path.stat().st_size
            if final_size == expected_size:
                print(f"✓ Download complete: {final_size:,} bytes")
                return True
            else:
                print(
                    f"⚠️  Size mismatch: got {final_size:,}, expected {expected_size:,}"
                )
                return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Download error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Download the model file."""
    print(f"Qwen2.5-1.5B Model Downloader")
    print(f"{'='*60}\n")

    # Create output directory
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    # Download
    success = download_with_progress(URL, OUTPUT_FILE, EXPECTED_SIZE)

    if success:
        print(f"\n🎉 Model ready at: {OUTPUT_FILE}")
        return 0
    else:
        print(f"\n⚠️  Download failed. You can rerun this script to resume.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
