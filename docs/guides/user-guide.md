# AI File Search - Complete User Guide

## Quick Start (30 seconds)
1. Start the application:
   ```bash
   python run_app.py
   ```
   This starts both the file watcher and the desktop interface.

2. Configure Watch Paths:
   - Go to the **Settings** page in the app.
   - Add any folder on your computer that you want to search.
   - The system will automatically index all supported files (PDF, DOCX, TXT, MD) in those folders.

3. Start Searching:
   - Go to the **Search** page.
   - Type your question.

## Key Features
- **Multi-Folder Support**: Watch any folder on your computer, not just `ai_search_docs`.
- **Real-time Indexing**: Changes are detected and indexed automatically.
- **Privacy First**: Everything runs locally. No data leaves your machine.

## Managing Watch Paths
You can manage which folders are indexed via the **Settings** page in the UI.
- **Add Path**: Enter the full path to a folder and click "Add".
- **Remove Path**: Click the "Remove" button next to a path.
- **Reindex**: If you suspect the index is out of sync, click "Rebuild Index".

## Supported File Types
- PDF (.pdf)
- Word (.docx)
- Text (.txt)
- Markdown (.md)

## Advanced: Manual Watcher Control
If you prefer running the watcher separately:
```bash
python smart_watcher.py start     # Start watching
python smart_watcher.py stop      # Stop watching
python smart_watcher.py status    # Check status
```

## Troubleshooting
**Watcher not starting?**
```bash
python smart_watcher.py status  # Check what's wrong
python run_watcher.py --dry-run # Test configuration
```

**Documents not appearing in search?**
- Check if the folder is added in Settings.
- Click "Rebuild Index" in Settings.
- Check logs in `logs/watcher.log`.
