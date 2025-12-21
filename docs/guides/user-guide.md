
    # AI File Search - Complete User Guide

Quick Start (30 seconds)
1. Start the smart watcher (watches ALL folders automatically):
python smart_watcher.py start

2. Add your documents to any folder in ai_search_docs/:
ai_search_docs/
├── my_research/      # Create any folder name
├── work_docs/        # Add your files here
└── personal/         # System auto-discovers everything!

3. Start searching with the web interface:
python -m streamlit run ui/app.py

Open: http://localhost:8501

Key Features
- Zero Configuration
- Add any folder to ai_search_docs/ - it's automatically discovered
- All folders watched by default - no manual setup needed
- Real-time indexing - changes appear in search within seconds

Smart Watcher Commands
python smart_watcher.py start     # Start watching (recommended)
python smart_watcher.py stop      # Stop watching
python smart_watcher.py status    # Check if running + show details
python smart_watcher.py restart   # Restart the watcher

Category Management (Optional)
python switch_documents.py discover  # See all auto-discovered categories
python switch_documents.py status    # Check what's enabled
python switch_documents.py research  # Focus search on 'research' folder only
python switch_documents.py all       # Search everything (default)

Folder Structure
Your project should look like this:
ai_search_docs/
├── my_research/      # Create any folder name
├── work_docs/        # Add your files here
└── personal/         # System auto-discovers everything!
extracts/             # Where AI extracts are saved
logs/                 # Logs for smart watcher and AI
prompts/              # Custom prompts for AI search

How It Works
1. Drop files anywhere in ai_search_docs/subfolders/
2. Watcher detects changes automatically
3. AI extracts and indexes content
4. Search with citations works immediately

Troubleshooting
Watcher not starting?
python smart_watcher.py status  # Check what's wrong
python run_watcher.py --dry-run # Test configuration

Documents not appearing in search?
python switch_documents.py status  # Check if category is enabled
python smart_watcher.py restart    # Restart the watcher

Pro Tips
1. Organize by purpose: Create folders like research/, manuals/, contracts/
2. Use descriptive names: Folder names become searchable categories
3. Mixed file types: PDFs, Word docs, text files all work
4. Nested folders: docs/2024/projects/ structures are fully supported
5. Real-time: No need to restart anything when adding files

You're All Set!
The AI File Search is now running with zero-config smart watching. Just add documents and start searching!

Happy Searching! 
