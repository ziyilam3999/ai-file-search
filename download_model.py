# download_model.py

from huggingface_hub import hf_hub_download
import pathlib
import sys

REPO_ID = "microsoft/Phi-3-mini-4k-instruct-gguf"
FILENAME = "Phi-3-mini-4k-instruct-q4.gguf"
DEST_DIR = pathlib.Path(__file__).parent / "ai_models"


print(f"📥 Downloading model '{FILENAME}' from '{REPO_ID}' into '{DEST_DIR}'...")

try:
    path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=DEST_DIR,
        local_dir_use_symlinks=False
    )
    print("✅ Model downloaded successfully!")
    print("📄 Saved at:", path)

except Exception as e:
    print("❌ Failed to download model.")
    print("Error:", e)
    sys.exit(1)
