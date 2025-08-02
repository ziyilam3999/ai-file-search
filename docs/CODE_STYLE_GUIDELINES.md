# Code Style Guidelines - AI File Search System

## CRITICAL: Emoji-Free Code Requirement

**For AI agents and developers: This codebase MUST remain emoji-free for cross-platform compatibility.**

### Why Emoji-Free?

1. **Cross-Platform Compatibility**: Emoji characters cause encoding issues in subprocess calls across Windows/Mac/Linux
2. **Professional Standards**: Text-based indicators are more professional and accessible
3. **Subprocess Reliability**: Prevents Unicode encoding errors in terminal operations
4. **AI Agent Compatibility**: Ensures consistent behavior across different AI development environments

### Prohibited Characters

**NEVER USE**: Emoji characters in any code files
- No Unicode emoticons (happy face, rocket, checkmark, X, etc.)
- No symbol pictographs (wrench, folder, computer, etc.)
- No status indicators using emoji

### Required Text Replacements

Use descriptive text prefixes instead of emoji:

| Emoji | Text Replacement |
|-----------|-------------------|
| checkmark | `SUCCESS:` or `COMPLETED:` |
| X mark | `ERROR:` or `FAILED:` |
| rocket | `STARTING:` or `LAUNCHING:` |
| folder | `FOLDER:` or `DIRECTORY:` |
| document | `FILE:` |
| wrench | `CONFIGURING:` or `SETUP:` |
| computer | `SYSTEM:` or `PROCESSING:` |
| target | `TARGET:` or `FOCUS:` |
| memo | `NOTE:` or `INFO:` |
| warning | `WARNING:` |
| magnifying glass | `SEARCHING:` or `ANALYZING:` |

### Code Examples

#### INCORRECT (with emoji):
```python
print("rocket Starting file watcher...")
logging.info("checkmark Index created successfully")
raise Exception("X mark Failed to load model")
```

#### CORRECT (emoji-free):
```python
print("STARTING: File watcher...")
logging.info("SUCCESS: Index created successfully")
raise Exception("ERROR: Failed to load model")
```
#### Validation Commands
Before committing code changes:
```python
# Check for emoji characters
python check_emoji_free.py

# Expected output for clean codebase:
# SUCCESS: Codebase is emoji-free!
```
#### AI Agent Instructions
IMPORTANT for AI agents working on this codebase:

Never introduce emoji characters in any file edits
Replace any existing emojis with appropriate text prefixes
Use descriptive text like "SUCCESS:", "ERROR:", "STARTING:" instead
Run validation with python check_emoji_free.py after changes
Check subprocess compatibility when modifying terminal operations
#### File Types Covered
This requirement applies to ALL text files:

Python files (*.py)
Markdown files (*.md)
Configuration files (*.yaml, *.yml, *.json)
Text files (*.txt)
Documentation files
Enforcement
Pre-commit: Run python check_emoji_free.py
CI/CD: Include emoji detection in automated tests
Code Review: Verify emoji-free requirement in all pull requests
Documentation: Maintain this guideline for all future contributors
#### Cross-Platform Benefits
Following this guideline ensures:

SUCCESS: Reliable subprocess execution on Windows PowerShell
SUCCESS: Consistent behavior on macOS Terminal
SUCCESS: Proper operation on Linux bash/zsh
SUCCESS: No Unicode encoding errors in automation scripts
SUCCESS: Professional, accessible user interfaces
Remember: Professional software uses descriptive text, not emoji characters. This ensures reliability, accessibility, and cross-platform compatibility.

