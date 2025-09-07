# File Watcher System Guide

Complete guide to the AI File Search real-time file monitoring system.

## Overview

The file watcher system provides automatic, real-time indexing of document changes using Python's `watchdog` library. It monitors the `sample_docs/` directory and all subdirectories for file changes.

## How File Watching Works

### Architecture
sample_docs/ # Monitored directory ├── category1/ # Automatically detected │ ├── document.pdf # Watched files │ └── notes.txt └── category2/ └── manual.docx

↓ File System Events ↓

File Watcher Daemon # Python watchdog.Observer ├── Detects Changes # Created, Modified, Deleted ├── Debounces Events # Prevents duplicate processing └── Queues Processing # Background worker thread

↓ Processing Pipeline ↓

Extract Text # PDF/DOCX → TXT
Generate Embeddings # sentence-transformers
Update Index # FAISS + SQLite
Update Citations # Map back to sample_docs/


### Supported File Types
- **PDF files** (`.pdf`) - Extracted using pdfminer.six
- **Word documents** (`.docx`) - Extracted using python-docx
- **Text files** (`.txt`) - Direct processing
- **Markdown files** (`.md`) - Direct processing

### Ignored Files
- Temporary files: `*.tmp`, `*.swp`, `*.bak`
- System files: `*.log`, `*.pyc`, `__pycache__`
- Version control: `.git/*`

## Starting and Stopping the Watcher

### Command Interface

```bash
# Start watcher (background process)
python smart_watcher.py start

# Start with verbose logging
python smart_watcher.py start --verbose

# Stop watcher
python smart_watcher.py stop

# Check status
python smart_watcher.py status

# Restart (stop + start)
python smart_watcher.py restart

Process Management
Background Operation:

Watcher runs as a separate background process
PID stored in logs/watcher.pid
Status tracked in watcher_status.json
Logs written to watcher.log

Process Control:
# Check if running
ps aux | grep watcher  # Linux/Mac
tasklist | findstr python  # Windows

# Manual kill (if needed)
kill $(cat logs/watcher.pid)  # Linux/Mac
taskkill /PID $(Get-Content logs/watcher.pid)  # Windows PowerShell

Watcher Configuration
Configuration File: watcher_config.yaml
# Directories to watch
watch_directories:
  - sample_docs

# File patterns
file_patterns:
  include:
    - "*.txt"
    - "*.pdf"
    - "*.docx" 
    - "*.md"
  ignore:
    - "*.tmp"
    - "*.log"
    - "*.pyc"
    - "__pycache__"
    - ".git"
    - "*.swp"
    - "*.bak"

# Timing settings
timing:
  debounce_seconds: 5        # Wait before processing changes
  max_wait_seconds: 30       # Maximum wait time
  nightly_reindex_time: "02:00"  # Full reindex schedule

# Performance settings
performance:
  max_memory_mb: 1024
  worker_threads: 2

  Auto-Discovery
The system automatically:

Scans sample_docs for new folders
Creates configuration for discovered categories
Starts watching new directories immediately
Updates index when folders are added/removed
File Change Processing
Event Flow
File System Event (create/modify/delete)
Debouncing (5-second delay to group related changes)
Queue Processing (background worker thread)
Text Extraction (if PDF/DOCX)
Embedding Generation (sentence-transformers)
Index Update (FAISS + SQLite)
Citation Mapping (extracts/ → sample_docs/)
Real-Time Updates
Detection Time: < 1 second
Processing Time: 2-5 seconds per file
Index Update: Real-time (no restart required)
Search Availability: Immediate after processing
Batch Processing
Multiple Files: Processed in batches for efficiency
Duplicate Events: Automatically deduplicated
Error Recovery: Failed files retry automatically
Memory Management: Batched to prevent memory issues

Monitoring and Troubleshooting
Status Checking
# Quick status
python smart_watcher.py status

# Detailed logs
tail -f logs/watcher.log

# Live monitoring
python tools/live_monitor.py

Common Issues
Watcher Won't Start:
# Check configuration
python run_watcher.py --dry-run

# Check dependencies
pip list | grep -E "(watchdog|psutil|pyyaml)"

# Check ports/permissions
python -c "import watchdog; print('OK')"

Files Not Being Indexed:
# Check if directory is watched
python switch_documents.py status

# Check file patterns
python run_watcher.py --dry-run

# Manual test
python tools/monitor_file_processing.py

Performance Issues:
# Check memory usage
python tools/live_monitor.py

# Reduce batch size in config
# Increase debounce_seconds in config

# Check disk space
df -h  # Linux/Mac
Get-WmiObject -Class Win32_LogicalDisk  # Windows

Log Analysis
Log Levels:

INFO: Normal operations (file processed, watcher started)
DEBUG: Detailed processing steps (enable with --verbose)
WARNING: Non-fatal issues (file skipped, permission denied)
ERROR: Processing failures (extraction failed, index error)

Key Log Patterns:
# Successful processing
grep "Successfully added document" logs/watcher.log

# Processing errors
grep "ERROR" logs/watcher.log

# Performance metrics
grep "processing took" logs/watcher.log

Advanced Features
Nightly Reindexing
Scheduled: 2:00 AM by default (configurable)
Purpose: Rebuild index from scratch for consistency
Duration: 30-60 seconds for typical document collections
Automatic: No user intervention required
Smart Folder Detection
New Folders: Automatically detected and added to watch list
Removed Folders: Gracefully handled (index entries cleaned up)
Nested Folders: Fully supported with recursive watching
Symlinks: Followed if they point to valid directories
Process Recovery
Crash Recovery: Automatically restarts on system reboot
Graceful Shutdown: Handles SIGTERM/SIGINT properly
State Persistence: Maintains processing queue across restarts
Lock Files: Prevents multiple instances
Integration with Other Components
With Search System
Real-time Updates: Search results reflect file changes immediately
Citation Accuracy: Citations always point to current file locations
Index Consistency: Automatic cleanup of deleted files
With UI System
Status Display: Web UI shows watcher status
Live Updates: Search results update without page refresh
Error Reporting: UI displays processing errors to users
With Testing System
Test Integration: Tests can start/stop watcher programmatically
Validation: Automated tests verify watcher functionality
Performance: Benchmarking includes watcher overhead

Deployment Considerations
Development Environment
# Start in foreground for debugging
python run_watcher.py --verbose

# Monitor in separate terminal
tail -f logs/watcher.log

Production Environment
# Use process manager (systemd, supervisor, etc.)
# Or start as background service
python smart_watcher.py start

# Monitor with cron
0 */6 * * * python smart_watcher.py status >> /var/log/watcher-health.log

Docker Deployment
# Ensure proper signal handling
CMD ["python", "smart_watcher.py", "start"]

# Mount watch directories
VOLUME ["/app/sample_docs", "/app/logs"]

Security Considerations
File Permissions: Watcher needs read access to sample_docs/
Process Permissions: Runs with user privileges (no root required)
Network Access: No external network connections required
Data Privacy: All processing happens locally
Performance Characteristics
Resource Usage
CPU: Low (< 5% during processing)
Memory: 200-500MB (depending on document size)
Disk I/O: Moderate during indexing, low during monitoring
Network: None (fully local operation)
Scalability
File Count: Tested with 1000+ documents
Directory Depth: No practical limit
File Size: Up to 100MB per file efficiently
Concurrent Changes: Handles batch updates well
This comprehensive guide covers all aspects of the file watcher system for both users and developers.
